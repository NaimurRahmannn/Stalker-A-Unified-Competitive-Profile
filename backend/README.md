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
- `ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS` (default: legacy
  `ATCODER_SYNC_COOLDOWN_SECONDS`, then `3600`)
- `ATCODER_CONNECT_TIMEOUT_SECONDS` (default: `3.05`)
- `ATCODER_READ_TIMEOUT_SECONDS` (default: `10`)
- `STALKER_EXTERNAL_USER_AGENT` (identifies STALKER to external providers)

AtCoderProblems submission-ingestion settings (all optional):

- `ATCODER_PROBLEMS_SYNC_ENABLED` (default: `True`)
- `ATCODER_PROBLEMS_BASE_URL`
- `ATCODER_PROBLEMS_TIMEOUT_SECONDS` (default: `10`)
- `ATCODER_PROBLEMS_MIN_REQUEST_INTERVAL_SECONDS` (default: `1.1`)
- `ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC` (default: `2`)
- `ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS` (default: `300`)

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
- `POST /api/v1/platform-accounts/<id>/sync/` — canonical platform sync; AtCoder
  independently refreshes official rating history and AtCoderProblems submissions
- `GET /api/v1/platform-accounts/<id>/atcoder-submissions/` — return cached AtCoder
  submission stats, source-specific cursor state, and the latest 20 submissions
- `POST /api/v1/platform-accounts/<id>/sync-submissions/` — temporary compatibility /
  development endpoint using the same cooldown-aware submission service as unified sync

Dashboard:

- `GET /api/v1/dashboard/me/` — returns `{ user, platforms: [{ ..., stats }] }`

Competitive programming analytics:

- `GET /api/v1/competitive-programming/codeforces/` returns the authenticated user's
  normalized Codeforces account, current stats, rating history, recent activity, and growth
  snapshots.
- `GET /api/v1/competitive-programming/atcoder/` returns the authenticated user's cached
  AtCoder account summary, combined/source sync state, Algorithm rating history, bounded recent
  submissions, completeness-aware stats, and normalized growth snapshots. This read never
  contacts either AtCoder provider.
- A successful Codeforces sync stores a bounded recent-activity list and creates a historical
  stats snapshot when the tracked values changed.

AtCoder Algorithm rating ingestion:

- AtCoder accounts use `POST /api/v1/platform-accounts/<id>/sync/` as the canonical combined
  entry point. It returns `success`, `partial`, or `failed`, plus structured `rating` and
  `submissions` source results with stable statuses/error codes and independent freshness.
- Sync reads only `/users/<handle>/history/json?contestType=algo`, validates and normalizes the
  complete response, and transactionally caches Algorithm rating events and derived stats.
- Rating and submission account cooldowns are independent and measured from each source's
  latest attempt. A fresh source is skipped without an external call while another eligible
  source can still run. Provider request throttling remains a separate protection.
- Each source persists atomically on its own. One source succeeding while the other fails
  produces `partial`, preserves both caches correctly, and advances only successful-source
  freshness. `last_synced_at` advances when at least one source actually refreshes successfully.
- Platform-account responses expose `atcoder_stats`, `atcoder_rating_history`, explicit
  handle-validation state, and separate ownership-verification state.
- Dashboard and public-profile reads never contact AtCoder. They continue to read STALKER's
  database only.

AtCoderProblems submission ingestion:

- Submission ingestion is independent from the official AtCoder rating-history sync.
- The provider's inclusive timestamp cursor is paired with the last submission ID. STALKER
  re-fetches the boundary second and relies on a database uniqueness constraint for safe overlap.
- Each validated page is persisted atomically with cursor advancement and metric recalculation.
- Backfill is limited by `ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC`; explicit `backfilling`,
  `caught_up`, and `blocked` states distinguish normal progress, completion, and the saturated
  same-timestamp boundary that cannot be advanced safely.
- The in-process limiter spaces provider-wide requests by more than one second by default. It
  does not coordinate across multiple application processes; distributed limiting is deferred.

AtCoder snapshot semantics:

- Combined sync records one coherent snapshot after both source attempts finish. Rating-only
  partial success still creates a useful snapshot, while a completed submission refresh is
  reflected immediately rather than leaving an intermediate incomplete snapshot.
- `PlatformStatsSnapshot.solved_count` is nullable. Incomplete AtCoder submission history is
  stored as `null` with `submission_stats_complete=false`, never as a fabricated zero.
- Codeforces snapshots continue storing exact integer solved counts.

Platform-account list/detail responses remain lightweight: they expose current summary and sync
state but not full AtCoder rating history. Heavy analytics live only at the dedicated endpoint.

## Notes

- `PlatformAccount` supports an 11-platform enum; `codeforces`, AtCoder Algorithm ratings, and
  incremental AtCoderProblems submissions are implemented. Problem metadata and difficulty
  enrichment remain out of scope.
- The sync action resolves a connector from the provider registry
  (`apps.connectors.services.get_connector`) keyed by `PlatformAccount.Platform`. The connector
  fetches and validates provider data before atomically persisting provider-specific rows,
  account sync state, and a deduplicated snapshot.
- Sync error taxonomy: invalid handles return `400`, provider/local throttling returns `429`,
  and disabled, denied, unavailable, or schema-incompatible providers return `503`.
- External calls are encapsulated in the connectors provider architecture for future platforms.
- Unit tests mock external Codeforces and AtCoder calls and do not hit live provider APIs.
