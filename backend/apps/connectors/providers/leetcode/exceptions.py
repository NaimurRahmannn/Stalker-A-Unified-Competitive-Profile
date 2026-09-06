from apps.connectors.base.exceptions import (
    ConnectorError,
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderTimeoutError,
)


class LeetCodeConfigurationError(ConnectorError):
    """Raised when the configured LeetCode adapter cannot be used safely."""


class LeetCodeUserNotFoundError(InvalidExternalAccountError):
    """Raised when the requested public LeetCode user does not exist."""


class LeetCodeInvalidResponseError(ProviderSchemaError):
    """Raised when provider data cannot satisfy the STALKER contract."""


class LeetCodeProviderUnavailableError(ExternalServiceError):
    """Raised when the configured LeetCode provider cannot serve a request."""


class LeetCodeProviderTimeoutError(ProviderTimeoutError):
    """Raised when the configured LeetCode provider times out."""


class LeetCodeProviderAccessError(ProviderAccessDeniedError):
    """Raised when provider authentication or access configuration is rejected."""


class LeetCodeProviderRateLimitError(ProviderRateLimitError):
    """Raised when the configured LeetCode provider throttles STALKER."""
