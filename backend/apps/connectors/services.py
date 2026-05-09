from apps.accounts.models import ExternalAccount
from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.providers.codeforces.connector import CodeforcesConnector


CONNECTOR_REGISTRY: dict[str, BaseConnector] = {
    ExternalAccount.Source.CODEFORCES: CodeforcesConnector(),
}


def get_connector(source: str) -> BaseConnector:
    connector = CONNECTOR_REGISTRY.get(source)
    if connector is None:
        raise UnsupportedSourceError(f"Unsupported source: {source}")
    return connector
