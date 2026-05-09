class ConnectorError(Exception):
    """Base connector error."""


class UnsupportedSourceError(ConnectorError):
    """Raised when source has no connector implementation."""


class ExternalServiceError(ConnectorError):
    """Raised when provider API is unavailable or returns unexpected errors."""


class InvalidExternalAccountError(ConnectorError):
    """Raised when provider handle/slug is invalid or not found."""
