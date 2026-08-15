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

## Notes

- `PlatformAccount` supports an 11-platform enum; `codeforces` is the only platform with an
  implemented connector and stats today (`CodeforcesStats`).
- The sync action resolves a connector from the provider registry
  (`apps.connectors.services.get_connector`) keyed by `PlatformAccount.Platform`, calls
  `CodeforcesConnector.fetch_normalized_profile(handle)`, and `update_or_create`s the
  `CodeforcesStats` row. Adding a new platform means writing a provider (client → connector →
  mapper) and registering it — no model or viewset changes.
- Sync error taxonomy: `InvalidExternalAccountError` → `400`, `ExternalServiceError` → `503`.
- External calls are encapsulated in the connectors provider architecture for future platforms.
- Unit tests mock external Codeforces API calls and do not hit real network APIs.
