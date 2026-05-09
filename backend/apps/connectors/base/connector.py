from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    source: str

    @abstractmethod
    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        raise NotImplementedError
