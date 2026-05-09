from apps.dashboard.selectors import get_dashboard_accounts


def build_dashboard_payload(user) -> dict:
    accounts = get_dashboard_accounts(user)
    return {
        "user": user,
        "accounts": accounts,
    }
