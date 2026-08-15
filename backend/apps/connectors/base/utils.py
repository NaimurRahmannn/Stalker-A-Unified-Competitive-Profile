from urllib.parse import quote


def normalize_handle(handle_or_slug: str) -> str:
    return handle_or_slug.strip()


def build_codeforces_profile_url(handle: str) -> str:
    return f"https://codeforces.com/profile/{handle}"


def build_atcoder_profile_url(handle: str) -> str:
    return f"https://atcoder.jp/users/{quote(handle, safe='')}"
