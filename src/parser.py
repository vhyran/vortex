from asyncio import StreamReader, StreamWriter, wait_for
from struct import pack
from sqlite3 import connect, Error as SQLiteError
from hashlib import sha1

from server import MySQLServer
from errors import DatabaseError
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# MySQL capability flags
CLIENT_PLUGIN_AUTH = 0x00080000  # Client supports authentication plugins


async def parse_client_packet(
    server: MySQLServer,
    reader: StreamReader,
    writer: StreamWriter,
    initial_sequence_id: int,
) -> None:
    """Parse incoming client packets and interact with SQLite.

    Handles the client handshake response, authenticates the user using mysql_native_password,
    and processes subsequent SQL queries by interacting with the SQLite backend.

    Args:
        server: The MySQLServer instance handling the connection.
        reader: Stream reader for client input.
        writer: Stream writer for server output.
        initial_sequence_id: Starting sequence ID for packet communication.
    """
    sequence_id = initial_sequence_id

    # Wait for client handshake response with a timeout
    try:
        data = await wait_for(reader.read(1024), timeout=5.0)
    except TimeoutError:
        logger.error("Timeout waiting for client handshake response")
        return

    if not data:
        logger.debug("No initial data received from client")
        return

    # Parse client handshake response
    packet_len = int.from_bytes(data[:3], "little")
    client_seq = data[3]
    client_capabilities = int.from_bytes(data[4:8], "little")
    max_packet_size = int.from_bytes(data[8:12], "little")
    charset = data[12]
    username_end = data.find(b"\x00", 23)

    logger.debug(f"Received client packet: {data.hex()}")
    logger.debug(
        f"Client capabilities: {hex(client_capabilities)}, Max packet size: {max_packet_size}, Charset: {charset}"
    )

    if not (client_capabilities & CLIENT_PLUGIN_AUTH):
        logger.warning("Client does not support plugin authentication")
        await server.send_packet(
            writer,
            b"\xff\x04\x04#28000Authentication plugin not supported",
            client_seq + 1,
        )
        return

    if username_end == -1:
        logger.warning("Malformed client handshake: no username found")
        await server.send_packet(
            writer, b"\xff\x04\x04#28000Access denied", client_seq + 1
        )
        return

    username = data[23:username_end].decode("utf-8", errors="ignore")
    auth_len = int.from_bytes(data[username_end + 1 : username_end + 2], "little")
    auth_response = data[username_end + 2 : username_end + 2 + auth_len]

    # mysql_native_password authentication
    if username != server._username:
        logger.warning(f"Username mismatch: {username} != {server._username}")
        await server.send_packet(
            writer, b"\xff\x04\x04#28000Access denied", client_seq + 1
        )
        return

    if server._password:
        password_hash = sha1(server._password.encode()).digest()
        stage1 = sha1(password_hash).digest()
        if server._auth_data is None:
            logger.error("Authentication data is missing")
            await server.send_packet(
                writer, b"\xff\x04\x04#28000Access denied", client_seq + 1
            )
            return
        stage2 = sha1(server._auth_data + stage1).digest()
        expected_response = bytes(a ^ b for a, b in zip(password_hash, stage2))
        if auth_response != expected_response:
            logger.warning(f"Password authentication failed for user: {username}")
            await server.send_packet(
                writer, b"\xff\x04\x04#28000Access denied", client_seq + 1
            )
            return

    # Send OK packet after successful authentication
    sequence_id = await server.send_packet(
        writer, b"\x00\x00\x00\x02\x00\x00\x00", client_seq + 1
    )
    logger.info(f"Client authenticated: {username}")

    # SQLite connection
    conn = connect(server._data_file)
    cursor = conn.cursor()

    try:
        while True:
            try:
                data = await wait_for(reader.read(1024), timeout=30.0)
            except TimeoutError:
                logger.debug("Timeout waiting for client query")
                break
            if not data:
                logger.debug("Client disconnected")
                break
            packet_len = int.from_bytes(data[:3], "little")
            client_seq = data[3]
            query = (
                data[4 : 4 + packet_len].decode("utf-8", errors="ignore")[1:].strip()
            )
            query_upper = query.upper()
            logger.debug(f"Received query: {query}")

            if query_upper.startswith("SELECT"):
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    sequence_id = await server.send_packet(
                        writer, pack("B", len(columns)), client_seq + 1
                    )
                    for col in columns:
                        col_def = (
                            b"\x03def\x00\x00\x00"
                            + pack("B", len(col))
                            + col.encode()
                            + b"\x0c\x21\x00\xff\x00\x00\xfc\x00\x00\x00\x00\x00"
                        )
                        sequence_id = await server.send_packet(
                            writer, col_def, sequence_id
                        )
                    sequence_id = await server.send_packet(
                        writer, b"\xfe\x00\x00\x02\x00", sequence_id
                    )
                    for row in rows:
                        row_data = b"".join(
                            pack("B", len(str(val).encode())) + str(val).encode()
                            for val in row
                        )
                        sequence_id = await server.send_packet(
                            writer, row_data, sequence_id
                        )
                    sequence_id = await server.send_packet(
                        writer, b"\xfe\x00\x00\x02\x00", sequence_id
                    )
                except SQLiteError as e:
                    raise DatabaseError(f"SQLite query failed: {e}", e)
            elif query_upper.startswith("USE"):
                sequence_id = await server.send_packet(
                    writer, b"\x00\x00\x00\x02\x00\x00\x00", client_seq + 1
                )
            elif query_upper == "SHOW DATABASES":
                sequence_id = await server.send_packet(writer, b"\x01", client_seq + 1)
                sequence_id = await server.send_packet(
                    writer,
                    b"\x03def\x00\x00\x00\x08Database\x00\x0c\x21\x00\xff\x00\x00\xfc\x00\x00\x00\x00\x00",
                    sequence_id,
                )
                sequence_id = await server.send_packet(
                    writer, b"\xfe\x00\x00\x02\x00", sequence_id
                )
                sequence_id = await server.send_packet(
                    writer, b"\x07sqlite3", sequence_id
                )
                sequence_id = await server.send_packet(
                    writer, b"\xfe\x00\x00\x02\x00", sequence_id
                )
            else:
                try:
                    cursor.execute(query)
                    conn.commit()
                    sequence_id = await server.send_packet(
                        writer, b"\x00\x00\x00\x02\x00\x00\x00", client_seq + 1
                    )
                except SQLiteError as e:
                    raise DatabaseError(f"SQLite command failed: {e}", e)

    finally:
        conn.close()
        writer.close()
        await writer.wait_closed()
