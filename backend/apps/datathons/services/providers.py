from dataclasses import dataclass
from typing import Callable

from django.conf import settings

from apps.connectors.providers.kaggle.provider import ProfileDocumentProvider


class CollectionError(Exception):
    def __init__(self, code: str, *, retryable: bool = False):
        self.code = code
        self.retryable = retryable
        super().__init__(code)


class ProviderUnavailable(CollectionError):
    def __init__(self):
        super().__init__("provider_unavailable", retryable=True)


class ProviderTimeout(CollectionError):
    def __init__(self):
        super().__init__("provider_timeout", retryable=True)


class ProviderRateLimited(CollectionError):
    def __init__(self):
        super().__init__("provider_rate_limited", retryable=True)


@dataclass(frozen=True)
class ProviderPolicy:
    max_concurrency: int
    min_interval_seconds: float
    max_attempts: int
    request_timeout_seconds: int
    max_response_bytes: int

    def validate(self):
        if (self.max_concurrency < 1 or self.min_interval_seconds < 0 or self.max_attempts < 1
                or self.request_timeout_seconds < 1 or self.max_response_bytes < 1_000):
            raise CollectionError("provider_policy_invalid")


@dataclass(frozen=True)
class ProviderRegistration:
    factory: Callable[[], ProfileDocumentProvider]
    policy: ProviderPolicy


# Only explicitly registered, authorized adapters may be selected. There is no live adapter.
PROVIDERS: dict[str, ProviderRegistration] = {}


def configured_provider() -> tuple[str, ProfileDocumentProvider, ProviderPolicy]:
    name = settings.KAGGLE_PROVIDER_NAME
    if not settings.KAGGLE_COLLECTION_ENABLED or name not in PROVIDERS:
        raise CollectionError("provider_disabled")
    registration = PROVIDERS[name]
    registration.policy.validate()
    return name, registration.factory(), registration.policy
