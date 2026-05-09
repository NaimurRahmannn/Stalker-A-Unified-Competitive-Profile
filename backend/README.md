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
python manage.py test apps.accounts apps.dashboard
```

## Implemented Endpoints

Auth:

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `GET /api/v1/auth/me/`

Accounts:

- `GET /api/v1/accounts/`
- `POST /api/v1/accounts/connect/`
- `POST /api/v1/accounts/<id>/sync/`

Dashboard:

- `GET /api/v1/dashboard/me/`

## Notes

- `source=codeforces` is currently the only supported connector source.
- External calls are encapsulated in connectors provider architecture for future platforms.
- Unit tests mock external Codeforces API calls and do not hit real network APIs.
