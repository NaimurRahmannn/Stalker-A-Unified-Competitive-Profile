def normalize_handle(handle_or_slug: str) -> str:
    return handle_or_slug.strip()


def build_codeforces_profile_url(handle: str) -> str:
    return f"https://codeforces.com/profile/{handle}"
