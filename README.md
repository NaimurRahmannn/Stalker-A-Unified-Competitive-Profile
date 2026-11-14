# STALKER

**A unified profile for competitive programming, cybersecurity, and hackathon work.**

STALKER brings platform accounts, cached activity, manually recorded achievements, and selected projects into one dashboard and shareable profile. Account owners control which hackathon projects and participations appear publicly.

## What the project supports

| Area | Current capabilities |
| --- | --- |
| Accounts | Registration, JWT login and refresh, and profile editing. |
| Competitive programming | Codeforces, AtCoder, and LeetCode account synchronization and cached analytics. The overview combines comparable metrics and identifies incomplete data. |
| Cybersecurity | CTFtime team synchronization, including team profile and yearly rankings. |
| Hackathons | Manual events, participations, projects, submissions, and achievements; owner-scoped search and filtering; privacy controls; public portfolios and project detail pages. |
| Devpost | Account linking and **user-supplied JSON** import with signed preview, field changes, import history, and possible duplicate review. |
| Datathons / Kaggle | Public username linking and private, self-reported Competition, Code, and Dataset rankings. Owners can edit or remove each track. Automatic collection is not enabled. |
| Contest calendar | The dashboard previews live and upcoming CLIST contests; `/contests` provides a paged list across platforms when backend API credentials are configured. |

The platform account model also recognizes other services, including CodeChef, GitHub, TryHackMe, Hack The Box, and DoraHacks. A recognized account type does not imply that synchronization or analytics are implemented for it.

## Architecture

```text
STALKER/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # Users and authentication
│   │   ├── connectors/     # Platform accounts, providers, and cached analytics
│   │   ├── dashboard/      # Authenticated summary
│   │   ├── hackathons/     # Manual records, Devpost import, and duplicate review
│   │   └── profiles/       # Public profile and hackathon portfolio APIs
│   └── config/             # Django settings and API routing
├── frontend/
│   ├── src/app/            # Next.js App Router pages
│   └── src/features/       # Feature components, API clients, and types
└── examples/               # Replaceable Devpost import example
```

The backend uses Django, Django REST Framework, SimpleJWT, and PostgreSQL or SQLite. The frontend uses Next.js 16, React 19, TypeScript, and Tailwind CSS. Provider sync results are stored in the backend; dashboard and public profile reads use stored data. The contest calendar is a separate cached CLIST feed.

## Run locally

Use Python 3.12 and a Node.js version compatible with the frontend dependencies. PostgreSQL is recommended for development that exercises row-lock concurrency; SQLite is available for a simpler local setup. Run the backend and frontend in separate terminals.

### 1. Backend

From the repository root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements/dev.txt
```

On macOS or Linux, activate the virtual environment with `source .venv/bin/activate` instead.

Create `backend/.env` with local values:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-unique-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

When all five PostgreSQL variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`) are set, Django uses PostgreSQL. Otherwise it uses `backend/db.sqlite3`. Both `.env` and the SQLite database are ignored by Git.

To show the optional contest calendar, add your CLIST account username and API key to `backend/.env` as `CLIST_USERNAME` and `CLIST_API`. Keep the key on the backend. The event feed caches each page of successful responses for 10 minutes and displays a retry state if CLIST is unavailable.

```powershell
python manage.py migrate
python manage.py runserver
```

The development API is available at `http://localhost:8000/api/v1/`. `manage.py` selects the development settings by default.

### 2. Frontend

In a second terminal, from the repository root:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

On macOS or Linux, use `cp .env.example .env.local`. The example sets `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`; keep the `/api/v1` suffix when changing the host. Open `http://localhost:3000`.

## Typical workflow

1. Register and sign in, then link a supported platform account.
2. Sync Codeforces, AtCoder, LeetCode, or CTFtime data from the platform account page when available.
3. Record hackathon work manually on `/hackathon`, or link a Devpost account and import your own JSON document. The file in `examples/` is a placeholder that must be replaced with real data before import.
4. Review the Devpost preview and confirm the import. Possible duplicate records can be marked related, distinct, or unresolved without merging either record.
5. Publish projects and participations independently. Visit `/profile/{username}` to see the public profile, or open a published project's detail page from its portfolio card.

## API overview

All routes below are relative to `/api/v1/`. Management routes require a JWT access token unless noted otherwise.

| Area | Representative routes |
| --- | --- |
| Accounts | `POST /accounts/register/`, `POST /accounts/login/`, `POST /accounts/token/refresh/`, `GET /accounts/me/` |
| Platform accounts | `GET/POST /platform-accounts/`, `POST /platform-accounts/{id}/sync/` |
| Competitive analytics | `GET /competitive-programming/overview/`, `/codeforces/`, `/atcoder/`, `/leetcode/` |
| Contest calendar | `GET /dashboard/events/?page=1` (authenticated, 50 contests per page) |
| Hackathon management | `GET /hackathons/overview/`; CRUD under `/hackathons/events/`, `/projects/`, `/participations/`, `/submissions/`, and `/achievements/` |
| Devpost import | `POST /hackathons/devpost/imports/preview/`; `GET/POST /hackathons/devpost/imports/` |
| Duplicate review | `GET/POST /hackathons/duplicate-reviews/`; `PATCH /hackathons/duplicate-reviews/{id}/` |
| Public profiles | `GET /profile/{username}/`, `/profile/{username}/hackathons/`, and `/profile/{username}/hackathons/projects/{projectId}/` — no authentication required |

Project discovery supports `search`, `source`, `visibility`, `technology`, `ordering`, `page`, and `page_size`. Event discovery supports `name`, `status`, `year`, `event_format`, `source`, `ordering`, and pagination. Invalid filters return validation errors; sorting uses explicit allowed values and stable tie breakers.

## Privacy and data integrity

- Hackathon projects and participations start private. Publishing one does not publish the other or reveal private relationships.
- Public project APIs return only published projects and eligible related work. Private or wrongly owned project details return 404.
- Imported Devpost metadata is protected from manual edits. Import preview is read-only; apply uses a signed preview and transactional checks.
- Achievement verification is an administrative action. Imported data, links, and duplicate-review decisions do not verify achievements.
- Duplicate-review decisions are owner-only metadata. **“Related” never merges, deletes, publishes, or reassigns records.**

## Verify changes

From `backend/`:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

From `frontend/`:

```powershell
npm run test:hackathons
npm run lint
npx tsc --noEmit
npm run build
```

The backend suite uses the configured database. PostgreSQL is required to exercise the row-lock concurrency tests; SQLite skips those cases. Frontend tests use local fixtures rather than live provider services.

## Current boundaries

Devpost data is imported from user-provided JSON; STALKER does not scrape or continuously synchronize Devpost. Duplicate suggestions use bounded URL matching and are not proof that two records are identical. The repository does not currently provide a configured Docker Compose development stack.

Hackathon phase notes are kept locally and ignored by Git. This README describes the functionality available in the tracked project.

