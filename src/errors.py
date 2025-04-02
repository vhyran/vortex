class VortexError(Exception):
    """Base exception class for Vortex library errors."""

    pass


class ConfigError(VortexError):
    """Raised when configuration is invalid or missing."""

    pass


class ProtocolError(VortexError):
    """Raised when MySQL protocol handling fails."""

    pass


class DatabaseError(VortexError):
    """Raised when SQLite operations fail."""

    def __init__(self, message, sqlite_error=None):
        super().__init__(message)
        self.sqlite_error = sqlite_error


class ConnectionError(VortexError):
    """Raised when client connection fails."""

    pass
