import html
import json
from datetime import datetime, timedelta
from html.parser import HTMLParser

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .domain import ParsedKaggleProfile
from .exceptions import KaggleDocumentError
from .identity import normalize_kaggle_identity


MAX_DOCUMENT_BYTES = 1_000_000


class _FixtureParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.seen_html = False
        self.in_data = False
        self.documents: list[str] = []
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "html":
            self.seen_html = True
        if tag == "script":
            attributes = dict(attrs)
            if attributes.get("type") == "application/json" and attributes.get("data-stalker-kaggle-profile") == "v1":
                self.in_data = True
                self._parts = []

    def handle_data(self, data):
        if self.in_data:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_data:
            self.documents.append("".join(self._parts))
            self.in_data = False


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise KaggleDocumentError("duplicate_field", "Duplicate profile field.")
        result[key] = value
    return result


def parse_profile_document(document: str, expected_username: str) -> ParsedKaggleProfile:
    """Parse only the versioned, synthetic/authorized offline document contract."""
    try:
        expected = normalize_kaggle_identity(expected_username)
    except ValueError as exc:
        raise KaggleDocumentError("invalid_identity", str(exc)) from exc
    if not isinstance(document, str) or len(document.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise KaggleDocumentError("document_too_large", "Profile document is invalid or too large.")
    parser = _FixtureParser()
    try:
        parser.feed(document)
        parser.close()
        if not parser.seen_html or len(parser.documents) != 1:
            raise KaggleDocumentError("unsupported_markup", "Expected one versioned profile document.")
        raw = json.loads(html.unescape(parser.documents[0]), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise KaggleDocumentError("invalid_document", "Profile document could not be parsed.") from exc
    if not isinstance(raw, dict) or set(raw) != {"username", "observed_at", "tracks"}:
        raise KaggleDocumentError("unsupported_schema", "Profile document schema is unsupported.")
    try:
        actual = normalize_kaggle_identity(raw["username"])
    except ValueError as exc:
        raise KaggleDocumentError("invalid_identity", "Profile identity is invalid.") from exc
    if actual.lookup_key != expected.lookup_key:
        raise KaggleDocumentError("identity_mismatch", "Profile identity does not match the expected username.")
    observed_at = parse_datetime(raw["observed_at"]) if isinstance(raw["observed_at"], str) else None
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is None:
        raise KaggleDocumentError("invalid_timestamp", "A timezone-aware observation time is required.")
    if observed_at > timezone.now() + timedelta(minutes=5):
        raise KaggleDocumentError("invalid_timestamp", "Observation time cannot be in the future.")
    if not isinstance(raw["tracks"], dict) or len(raw["tracks"]) > 3:
        raise KaggleDocumentError("invalid_tracks", "Profile tracks are invalid.")
    return ParsedKaggleProfile(actual.username, observed_at, raw["tracks"])
