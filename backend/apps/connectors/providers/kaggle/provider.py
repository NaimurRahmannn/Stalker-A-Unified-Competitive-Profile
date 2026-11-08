from pathlib import Path
from typing import Protocol

from .exceptions import KaggleDocumentError
from .parser import MAX_DOCUMENT_BYTES


class ProfileDocumentProvider(Protocol):
    def load(self, expected_username: str) -> str: ...


class OfflineFixtureProvider:
    """Reads a local file only; there is deliberately no live provider."""

    def __init__(self, path: Path):
        self.path = path

    def load(self, expected_username: str) -> str:
        try:
            if self.path.stat().st_size > MAX_DOCUMENT_BYTES:
                raise KaggleDocumentError("document_too_large", "Profile document is too large.")
            return self.path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise KaggleDocumentError("invalid_document", "Profile document could not be read.") from exc
