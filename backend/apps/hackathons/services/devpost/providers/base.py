"""Provider contract: acquire structured data without performing persistence.

Future network providers require an explicit authorization and configuration
decision. No network provider is registered in Phase 3.
"""

from typing import Any, Protocol


class StructuredDataProvider(Protocol):
    input_method: str

    def acquire(self, supplied: Any) -> dict: ...
