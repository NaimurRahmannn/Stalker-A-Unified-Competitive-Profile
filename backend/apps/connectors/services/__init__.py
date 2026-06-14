from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.models import PlatformAccount
from apps.connectors.providers.codeforces.connector import CodeforcesConnector


CONNECTOR_REGISTRY: dict[str, BaseConnector] = {
    PlatformAccount.Platform.CODEFORCES: CodeforcesConnector(),
}


def get_connector(source: str) -> BaseConnector:
    connector = CONNECTOR_REGISTRY.get(source)
    if connector is None:
        raise UnsupportedSourceError(f"Unsupported source: {source}")
    return connector
