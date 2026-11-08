import re
from dataclasses import dataclass
from urllib.parse import urlsplit


# Conservative local policy. Kaggle does not publish a complete username grammar.
_USERNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}\Z", re.ASCII)


@dataclass(frozen=True)
class KaggleIdentity:
    username: str
    profile_url: str
    lookup_key: str


def normalize_kaggle_identity(value: str) -> KaggleIdentity:
    if not isinstance(value, str):
        raise ValueError("Enter a Kaggle username or profile URL.")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("Kaggle username contains control characters.")
    value = value.strip()
    if not value:
        raise ValueError("Kaggle username cannot be empty.")
    if "://" in value or value.startswith("www.") or "/" in value or "?" in value or "#" in value:
        try:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or parsed.netloc.lower() not in {"kaggle.com", "www.kaggle.com"}
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port is not None
                or parsed.query
                or parsed.fragment
                or "?" in value
                or "#" in value
                or not parsed.path.startswith("/")
                or parsed.path.count("/") != 1
            ):
                raise ValueError
            username = parsed.path[1:]
        except (ValueError, AttributeError) as exc:
            raise ValueError("Enter a canonical HTTPS Kaggle profile URL.") from exc
    else:
        username = value
    if not _USERNAME.fullmatch(username):
        raise ValueError("Kaggle username must contain 1–50 ASCII letters, digits, underscores or hyphens.")
    return KaggleIdentity(username, f"https://www.kaggle.com/{username}", username.casefold())
