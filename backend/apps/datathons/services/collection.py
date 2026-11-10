from dataclasses import dataclass
from datetime import datetime

from django.db import DatabaseError

from apps.connectors.providers.kaggle.exceptions import KaggleDocumentError
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.connectors.providers.kaggle.normalizer import normalize_profile
from apps.connectors.providers.kaggle.parser import parse_profile_document
from apps.datathons.models import KaggleProfile
from apps.datathons.persistence import persist_kaggle_profile_statistics

from .providers import CollectionError, configured_provider


@dataclass(frozen=True)
class CollectionResult:
    profile_id: int
    observed_at: datetime
    track_count: int


def collect_kaggle_profile(profile: KaggleProfile, provider=None, policy=None) -> CollectionResult:
    """Load and validate one document, then use the Phase 1 transactional writer."""
    try:
        identity = normalize_kaggle_identity(profile.username)
    except ValueError as exc:
        raise CollectionError("invalid_identity") from exc
    if identity.lookup_key != profile.normalized_username or identity.profile_url != profile.profile_url:
        raise CollectionError("identity_mismatch")
    if provider is None:
        _, provider, policy = configured_provider()
    try:
        document = provider.load(identity.username)
        if policy is not None and len(document.encode("utf-8")) > policy.max_response_bytes:
            raise CollectionError("document_too_large")
        data = normalize_profile(parse_profile_document(document, identity.username))
        if normalize_kaggle_identity(data.username).lookup_key != identity.lookup_key:
            raise CollectionError("identity_mismatch")
        persisted = persist_kaggle_profile_statistics(profile, data)
    except KaggleDocumentError as exc:
        raise CollectionError(exc.code) from exc
    except DatabaseError as exc:
        raise CollectionError("persistence_failure") from exc
    return CollectionResult(persisted.pk, data.observed_at, len(data.tracks))
