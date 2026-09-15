from apps.connectors.base.exceptions import (
    ConnectorError,
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderTimeoutError,
)


class CTFtimeConfigurationError(ConnectorError):
    """Raised when the configured CTFtime adapter cannot be used safely."""


class CTFtimeTeamNotFoundError(InvalidExternalAccountError):
    """Raised when the requested public CTFtime team does not exist."""


class CTFtimeInvalidResponseError(ProviderSchemaError):
    """Raised when provider data cannot satisfy the STALKER contract."""


class CTFtimeProviderUnavailableError(ExternalServiceError):
    """Raised when the configured CTFtime provider cannot serve a request."""


class CTFtimeProviderTimeoutError(ProviderTimeoutError):
    """Raised when the configured CTFtime provider times out."""


class CTFtimeProviderAccessError(ProviderAccessDeniedError):
    """Raised when provider authentication or access configuration is rejected."""


class CTFtimeProviderRateLimitError(ProviderRateLimitError):
    """Raised when the configured CTFtime provider throttles STALKER."""
