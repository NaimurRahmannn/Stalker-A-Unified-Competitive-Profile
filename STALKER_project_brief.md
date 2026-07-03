# STALKER — Project Brief

## What it is
A unified competitive-profile platform. Users connect handles from competitive programming, CTF, datathon, and hackathon platforms, and Stalker aggregates them into one dashboard + shareable public profile with progress analytics. Inspired by StopStalk, but broader (not CP-only) and built on stored/synced data rather than fragile live scraping.

**Positioning:** a "unified technical growth dashboard," not a stats scraper. Value comes from analytics, milestones, and a shareable identity — not raw fetching. Public profile at `/profile/{username}` is the core shareable artifact.

## Stack
- **Backend:** Django + DRF, JWT auth (djangorestframework-simplejwt), python-decouple, django-cors-headers, `requests`. PostgreSQL with SQLite fallback. Layered: thin views → services (business logic) → connectors (external APIs). Provider-registry pattern so each new platform = one new provider + one registry entry.
- **Frontend:** Next.js 16 (App Router) / React 19, TypeScript, Tailwind v4, axios, react-hook-form + zod, sonner. Feature-based structure (`features/{auth,dashboard,platforms,profile}` each with `api.ts`/`types.ts`).

## Target platforms (build order)
CP core first: **Codeforces (done)** → CodeChef → AtCoder → LeetCode. Then Kaggle (datathon), CTFtime (CTF), hackathons (Devpost/DoraHacks — mostly manual entry, no clean API). Codeforces and CTFtime have solid official APIs; LeetCode and hackathons are fragile → treat as lower priority / manual.

## Backend architecture (current, working)
- `PlatformAccount` model: 11-platform enum, unique `(user, platform)`, handle, is_verified, last_synced_at.
- `CodeforcesStats` model: rating, max_rating, rank, max_rank, solved/attempted/accepted counts, contest_count, timestamps, raw JSON blobs.
- Connector chain: `base/connector.py` (abstract `BaseConnector`) → `providers/codeforces/` (`client.py` → `connector.py` → `mapper.py`) → registry in `services/__init__.py` (`get_connector`).
- The mapper computes **real** solved/attempted/contest stats by deduping submissions on `(contestId, index)` — verified working, fetches live Codeforces data correctly.
- `PlatformAccountViewSet` with `POST .../sync/` action.

## Key endpoints
- Auth: `POST /accounts/register/`, `POST /accounts/login/` (JWT), `POST /accounts/token/refresh/`, `GET /accounts/me/`
- Platforms: `GET/POST /connectors/platform-accounts/`, `POST /connectors/platform-accounts/{id}/sync/`, `DELETE .../{id}/`
- Dashboard: `GET /dashboard/me/` → returns `{ user, platforms: [{ ..., stats }] }`

## Status
- ✅ **Backend Codeforces slice: complete and working end-to-end.** Consolidated (an earlier duplicate `ExternalAccount`/`ProfileSnapshot` track was removed).
- ✅ Frontend auth wired to real API (`features/auth/api.ts`).
- ❌ **Frontend does NOT call the platform/dashboard API yet.** `features/platforms/api.ts` and `features/dashboard/api.ts` are empty TODO stubs; dashboard renders mock data from `features/dashboard/data.ts`; platforms page is a one-line stub. Dashboard UI components (metric cards, sparkline, technical-journey, connected-platforms) are built but fed fake data.

## Immediate next task: close the loop
Make one real journey work: **register → login → connect Codeforces handle → sync → see real stats.** Auth works; the two missing links are:
1. `features/platforms/api.ts` (list/connect/sync/delete) + a real platforms page (add-handle form, connected-accounts list with status/last-synced, per-account Sync button) + fill `platforms/types.ts` to mirror the serializer.
2. `features/dashboard/api.ts` (`getDashboard`) + swap dashboard off mock data, mapping the real `/dashboard/me/` response into existing components.

**Watch out for:** `NEXT_PUBLIC_API_BASE_URL` prefix must match `config/urls.py` mounts (connectors live at `/connectors/...`, auth at `/accounts/...`) — a base-URL mismatch silently breaks the first real fetch.

## After the loop closes
Public `profile/{username}` page → then a second connector (CodeChef or LeetCode) to prove the provider pattern scales.

## Engineering principles (agreed)
- Build small **vertical slices** end-to-end, one platform at a time; keep the product always usable.
- Don't force a fake "universal rating" — use per-platform stats + a custom consistency/activity score.
- Design for change: new platform must not break existing code.
- Later (not now): Celery/Redis background sync, milestone tracker ("+143 to Expert"), streaks/heatmap, friend comparison, shareable card, insights. Respect Codeforces rate limit (~1 req/2s) → add sync cooldown before scaling.

**Repo:** github.com/NaimurRahmannn/Stalker-A-Unified-Competitive-Profile
