# Progress Tracker Backend (Milestone 1)

This backend currently implements the first milestone for `progress-tracker`:

- User registration
- User login via JWT
- Authenticated `me` endpoint
- Connect a Codeforces handle
- Verify handle through official Codeforces public API (`user.info`)
- Store normalized profile snapshot data
- Fetch dashboard summary from backend-stored data

## Current Backend Structure

```text
backend/
├── apps/
│   ├── accounts/
│   ├── common/
│   ├── connectors/
│   ├── dashboard/
│   └── hackathons/          # untouched for future milestones
├── config/
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── .env
└── manage.py
```

## Tech Stack

- Django
- Django REST Framework
- djangorestframework-simplejwt
- python-decouple
- django-cors-headers
- requests
- PostgreSQL-ready config with SQLite fallback

## Environment Variables

Configured using `python-decouple` and `.env`.

Required for Django:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (True/False)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `CORS_ALLOWED_ORIGINS` (comma-separated)

AtCoder synchronization safety settings (all optional):

- `ATCODER_HISTORY_SYNC_ENABLED` (default: `True`)
- `ATCODER_SYNC_COOLDOWN_SECONDS` (default: `3600`)
- `ATCODER_CONNECT_TIMEOUT_SECONDS` (default: `3.05`)
- `ATCODER_READ_TIMEOUT_SECONDS` (default: `10`)
- `STALKER_EXTERNAL_USER_AGENT` (identifies STALKER to external providers)

Optional PostgreSQL variables:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

Behavior:

- If all PostgreSQL variables above are set, PostgreSQL is used.
- If any are missing, backend falls back to SQLite (`backend/db.sqlite3`).

## Setup

From `backend/`:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
```

## Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Run Server

```bash
python manage.py runserver
```

## Run Tests

```bash
python manage.py test
```

## Implemented Endpoints

All endpoints are served under the `/api/v1/` prefix.

Auth / Accounts:

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/login/` (JWT — `TokenObtainPair`)
- `POST /api/v1/accounts/token/refresh/`
- `GET /api/v1/accounts/me/`
- `PATCH /api/v1/accounts/me/update/`

Platform accounts (connectors):

- `GET /api/v1/platform-accounts/` — list the authenticated user's platform accounts
- `POST /api/v1/platform-accounts/` — add a platform account (`platform`, `handle`)
- `GET /api/v1/platform-accounts/<id>/` — retrieve one
- `PATCH /api/v1/platform-accounts/<id>/` — update the handle
- `DELETE /api/v1/platform-accounts/<id>/` — remove it
- `POST /api/v1/platform-accounts/<id>/sync/` — verify the handle and refresh stats via the platform connector

Dashboard:

- `GET /api/v1/dashboard/me/` — returns `{ user, platforms: [{ ..., stats }] }`

Competitive programming analytics:

- `GET /api/v1/competitive-programming/codeforces/` returns the authenticated user's
  normalized Codeforces account, current stats, rating history, recent activity, and growth
  snapshots.
- A successful Codeforces sync stores a bounded recent-activity list and creates a historical
  stats snapshot when the tracked values changed.

AtCoder Algorithm rating ingestion:

- AtCoder accounts use the same `POST /api/v1/platform-accounts/<id>/sync/` entry point.
- Sync reads only `/users/<handle>/history/json?contestType=algo`, validates and normalizes the
  complete response, and transactionally caches Algorithm rating events and derived stats.
- AtCoder's configurable cooldown is measured from the latest attempt, including failed
  provider calls, while `last_synced_at` continues to mean the last successful synchronization.
- Platform-account responses expose `atcoder_stats`, `atcoder_rating_history`, explicit
  handle-validation state, and separate ownership-verification state.
- Dashboard and public-profile reads never contact AtCoder. They continue to read STALKER's
  database only.

## Notes

- `PlatformAccount` supports an 11-platform enum; `codeforces` and AtCoder Algorithm rating
  history have implemented connectors. AtCoder submissions and AtCoderProblems are not part of
  this phase.
- The sync action resolves a connector from the provider registry
  (`apps.connectors.services.get_connector`) keyed by `PlatformAccount.Platform`. The connector
  fetches and validates provider data before atomically persisting provider-specific rows,
  account sync state, and a deduplicated snapshot.
- Sync error taxonomy: invalid handles return `400`, provider/local throttling returns `429`,
  and disabled, denied, unavailable, or schema-incompatible providers return `503`.
- External calls are encapsulated in the connectors provider architecture for future platforms.
- Unit tests mock external Codeforces and AtCoder calls and do not hit live provider APIs.
