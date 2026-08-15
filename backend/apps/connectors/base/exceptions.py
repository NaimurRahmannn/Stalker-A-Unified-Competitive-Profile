class ConnectorError(Exception):
    """Base connector error."""


class UnsupportedSourceError(ConnectorError):
    """Raised when source has no connector implementation."""


class ExternalServiceError(ConnectorError):
    """Raised when provider API is unavailable or returns unexpected errors."""


class InvalidExternalAccountError(ConnectorError):
    """Raised when provider handle/slug is invalid or not found."""


class ProviderRateLimitError(ExternalServiceError):
    """Raised when an external provider throttles synchronization."""


class ProviderAccessDeniedError(ExternalServiceError):
    """Raised when an external provider refuses access to an endpoint."""


class ProviderSchemaError(ExternalServiceError):
    """Raised when a provider response no longer matches the expected schema."""


class ProviderSyncDisabledError(ExternalServiceError):
    """Raised when synchronization is disabled by an application kill switch."""
