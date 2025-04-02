from asyncio import start_server, StreamReader, StreamWriter, Server, TimeoutError
from struct import pack
from dataclasses import dataclass
from typing import Optional, Self

import os
import logging

from errors import ConnectionError, ProtocolError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@dataclass
class MySQLServer:
    """A MySQL-compatible server using SQLite as the backend."""

    _host: str = "127.0.0.1"
    _port: int = 3306
    _username: str = "vortex"
    _password: str = ""
    _server_version: str = "5.7.0-custom"
    _auth_plugin: str = "mysql_native_password"
    _auth_data: Optional[bytes] = None
    _capability_flags: int = 0xA0D7FF  # CLIENT_LONG_PASSWORD | CLIENT_FOUND_ROWS | CLIENT_LONG_FLAG | CLIENT_CONNECT_WITH_DB | CLIENT_PROTOCOL_41 | CLIENT_SECURE_CONNECTION | CLIENT_PLUGIN_AUTH
    _charset: int = 33  # UTF-8 (utf8mb4)
    _status_flags: int = 0x0002  # SERVER_STATUS_AUTOCOMMIT
    _data_file: str = "/tmp/sqlite.db"
    server: Optional[Server] = None

    def config(
        self,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        server_version: Optional[str] = None,
        auth_plugin: Optional[str] = None,
        auth_data: Optional[bytes] = None,
        capability_flags: Optional[int] = None,
        charset: Optional[int] = None,
        status_flags: Optional[int] = None,
        data_file: Optional[str] = None,
    ) -> Self:
        self._host = host if host is not None else self._host
        self._port = port if port is not None else self._port
        self._username = username if username is not None else self._username
        self._password = password if password is not None else self._password
        self._server_version = (
            server_version if server_version is not None else self._server_version
        )
        self._auth_plugin = (
            auth_plugin if auth_plugin is not None else self._auth_plugin
        )
        self._auth_data = auth_data if auth_data is not None else self._auth_data
        self._capability_flags = (
            capability_flags if capability_flags is not None else self._capability_flags
        )
        self._charset = charset if charset is not None else self._charset
        self._status_flags = (
            status_flags if status_flags is not None else self._status_flags
        )
        self._data_file = data_file if data_file is not None else self._data_file

        if not self._auth_data:
            self._auth_data = os.urandom(
                20
            )  # Random 20-byte salt for mysql_native_password
        elif len(self._auth_data) < 20:
            self._auth_data = self._auth_data.ljust(20, b"\x00")[:20]

        return self

    async def send_packet(
        self, writer: StreamWriter, payload: bytes, sequence_id: int
    ) -> int:
        """Send a MySQL protocol packet to the client."""
        if len(payload) > 0xFFFFFF:
            raise ProtocolError("Payload exceeds MySQL packet size limit")
        packet = pack("<I", len(payload))[:3] + pack("B", sequence_id) + payload
        try:
            writer.write(packet)
            await writer.drain()
        except (OSError, TimeoutError) as e:
            raise ConnectionError(f"Failed to send packet: {e}")
        return sequence_id + 1

    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Handle an incoming client connection with MySQL handshake."""
        client_addr = writer.get_extra_info("peername") or ("unknown", "unknown")
        logger.info(f"Client connected - IP: {client_addr[0]}, Port: {self._port}")

        # Construct initial handshake packet (Protocol 10)
        handshake = (
            b"\x0a"  # Protocol version 10
            + self._server_version.encode()
            + b"\x00"  # Server version, null-terminated
            + pack("<I", 1)  # Connection ID
            + (
                self._auth_data[:8] if self._auth_data else b"\x00" * 8
            )  # Auth plugin data part 1 (8 bytes)
            + b"\x00"  # Filler
            + pack("<H", self._capability_flags & 0xFFFF)  # Lower capability flags
            + pack("B", self._charset)  # Character set
            + pack("<H", self._status_flags)  # Status flags
            + pack("<H", self._capability_flags >> 16)  # Upper capability flags
            + pack(
                "B", 21
            )  # Auth plugin data length (20 bytes + 1 for null terminator)
            + b"\x00" * 10  # Reserved
            + (
                self._auth_data[8:] if self._auth_data else b"\x00" * 12
            )  # Auth plugin data part 2 (remaining 12 bytes)
            + self._auth_plugin.encode()
            + b"\x00"  # Auth plugin name, null-terminated
        )
        logger.debug(f"Sending handshake packet: {handshake.hex()}")
        sequence_id = await self.send_packet(writer, handshake, 0)

        from parser import parse_client_packet

        await parse_client_packet(self, reader, writer, sequence_id)

    async def start(self) -> None:
        """Start the server on the configured host and port."""
        if self.server is not None:
            raise RuntimeError("Server is already running")
        try:
            self.server = await start_server(self.handle_client, self._host, self._port)
            await self.server.serve_forever()
        except OSError as e:
            raise ConnectionError(f"Failed to start server: {e}")

    async def stop(self) -> None:
        """Stop the server and close all connections."""
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

    async def __aenter__(self) -> "MySQLServer":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()
