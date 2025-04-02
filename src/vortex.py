"""Vortex Command-Line Interface.

This module provides the entry point for running the Vortex server, a MySQL-compatible
SQLite server. It supports loading configuration from a TOML file, overriding settings
via command-line arguments, creating a default config file, and running the server
asynchronously with detailed logging. The server can be customized for host, port,
authentication, and database file location.

Features:
- Load configuration from a TOML file (default: ~/.config/vortex/config.toml).
- Create a default config file if it doesn't exist with the --create-config flag.
- Override config settings via CLI arguments.
- Verbose mode for debug logging.
- Graceful shutdown on interrupt.

Usage:
    python -m vortex --help
    python -m vortex --config custom.toml --verbose
    python -m vortex --host 127.0.0.1 --port 3308 --create-config
"""

from asyncio import run, Future
from os import makedirs, path
from sys import exit
from typing import Dict, Optional
from argparse import ArgumentParser
from logging import basicConfig, getLogger, DEBUG, StreamHandler
from toml import load, dump, TomlDecodeError

from server import MySQLServer
from errors import ConfigError

# Constants
DEFAULT_CONFIG_PATH = path.expanduser("~/.config/vortex/config.toml")
DEFAULT_CONFIG_DIR = path.dirname(DEFAULT_CONFIG_PATH)
VERSION = "0.1.0-alpha"

# Default configuration template
DEFAULT_CONFIG = {
    "server": {
        "host": "localhost",
        "port": 3307,
        "username": "vortex",
        "password": "",
        "data_file": "/tmp/vortex.db",
    }
}

# Configure logging
basicConfig(
    level=DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[StreamHandler()],
)
logger = getLogger("vortex")


def load_config(config_path: str) -> Dict[str, dict]:
    """Load server configuration from a TOML file.

    Args:
        config_path (str): Path to the TOML configuration file.

    Returns:
        Dict[str, dict]: Configuration dictionary with server settings.

    Raises:
        ConfigError: If the config file is missing or contains invalid TOML.
    """
    if not path.exists(config_path):
        raise ConfigError(f"Configuration file not found at {config_path}")
    try:
        with open(config_path, "r") as f:
            config = load(f)
        if "server" not in config:
            raise ConfigError("Missing 'server' section in config file")
        return config
    except TomlDecodeError as e:
        raise ConfigError(f"Invalid TOML syntax in {config_path}: {e}")


def create_default_config(config_path: str) -> None:
    """Create a default configuration file if it doesn't exist.

    Args:
        config_path (str): Path where the config file should be created.

    Raises:
        ConfigError: If the directory cannot be created or file cannot be written.
    """
    if path.exists(config_path):
        logger.debug(f"Config file already exists at {config_path}")
        return

    try:
        makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
        with open(config_path, "w") as f:
            dump(DEFAULT_CONFIG, f)
        logger.info(f"Created default config file at {config_path}")
    except OSError as e:
        raise ConfigError(f"Failed to create config file at {config_path}: {e}")


def validate_config(config: Dict[str, Optional[str | int]]) -> None:
    """Validate server configuration values.

    Args:
        config (Dict[str, Optional[str | int]]): Server configuration dictionary.

    Raises:
        ConfigError: If any configuration value is invalid.
    """
    port = config.get("port")
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ConfigError(f"Invalid port: {port} (must be 1-65535)")
    if not config.get("host"):
        raise ConfigError("Host cannot be empty")
    if not config.get("data_file"):
        raise ConfigError("Data file path cannot be empty")
    if not isinstance(config.get("username"), str):
        raise ConfigError("Username must be a string")
    if not isinstance(config.get("password"), str):
        raise ConfigError("Password must be a string")


def main() -> None:
    """Command-line interface for running the Vortex server.

    Parses command-line arguments, loads or creates configuration, and starts the
    Vortex server. Supports overriding config values, creating a default config,
    and adjusting log verbosity.

    Command-line options:
        --config PATH        Path to TOML config file (default: ~/.config/vortex/config.toml)
        --create-config      Create a default config file if it doesn't exist
        --host HOST          Server host (overrides config)
        --port PORT          Server port (overrides config)
        --username USER      Username (overrides config)
        --password PASS      Password (overrides config)
        --data-file PATH     SQLite database file (overrides config)
        --verbose            Enable debug logging
        --version            Show version and exit
    """
    parser = ArgumentParser(description="Vortex: MySQL-compatible SQLite server")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to TOML config file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a default config file if it doesn't exist",
    )
    parser.add_argument("--host", help="Server host (overrides config)")
    parser.add_argument("--port", type=int, help="Server port (overrides config)")
    parser.add_argument("--username", help="Username (overrides config)")
    parser.add_argument("--password", help="Password (overrides config)")
    parser.add_argument("--data-file", help="SQLite database file (overrides config)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Vortex {VERSION}",
        help="Show version and exit",
    )
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(DEBUG)
        logger.debug("Verbose logging enabled")

    # Handle config creation
    if args.create_config or not path.exists(args.config):
        try:
            create_default_config(args.config)
        except ConfigError as e:
            logger.error(f"Failed to create config: {e}")
            exit(1)

    # Load configuration
    try:
        config = load_config(args.config)
        server_config = config["server"]
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)

    # Apply CLI overrides
    server_config["host"] = args.host or server_config.get("host")
    server_config["port"] = args.port or server_config.get("port")
    server_config["username"] = args.username or server_config.get("username")
    server_config["password"] = args.password or server_config.get("password")
    server_config["data_file"] = args.data_file or server_config.get("data_file")

    # Validate configuration
    try:
        validate_config(server_config)
    except ConfigError as e:
        logger.error(f"Invalid configuration: {e}")
        exit(1)

    async def run_server() -> None:
        """Run the Vortex server with the specified configuration."""
        try:
            server = MySQLServer().config(
                host=server_config["host"],
                port=server_config["port"],
                username=server_config["username"],
                password=server_config["password"],
                data_file=server_config["data_file"],
            )
            async with server:
                logger.info(f"Server started on {server._host}:{server._port}")
                logger.debug(f"Using config: {server_config}")
                await Future()  # Run indefinitely
        except Exception as e:
            logger.error(f"Server failed: {e}")
            raise

    # Start the server
    try:
        logger.info("Initializing Vortex server...")
        run(run_server())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
