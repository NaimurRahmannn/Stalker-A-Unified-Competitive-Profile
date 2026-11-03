# Phase 4: Public Hackathon portfolio

## Scope and architecture

Phase 4 lets owners publish Hackathon projects and participations independently and displays only eligible records on the existing public profile. It reuses `HackathonProject.is_public` and `HackathonParticipation.is_public`; no database migration or verification workflow is added. Manual records and Devpost imports remain private by default. The Devpost importer does not write `is_public`, so re-imports retain the owner's choice.

The authenticated dashboard uses dedicated visibility actions. The public profile uses separate queryset predicates and serializers in `apps.profiles.hackathon_public`. It does not reuse owner management serializers or authenticated overview counts. Each public collection is independently paginated. The existing profile response adds a small Hackathon summary while keeping its previous fields.

## Visibility API

Both endpoints require authentication and use owner-scoped querysets, a database transaction, and `SELECT FOR UPDATE` on the record. They accept only a JSON Boolean `is_public`, reject other fields and types with HTTP 400, and return HTTP 404 for inaccessible or missing records. Repeating the same setting returns the current state without rewriting the row.

| Endpoint | Request | Success response |
| --- | --- | --- |
| `PATCH /api/v1/hackathons/projects/{id}/visibility/` | `{ "is_public": true }` | `{ "id": 1, "is_public": true }` |
| `PATCH /api/v1/hackathons/participations/{id}/visibility/` | `{ "is_public": false }` | `{ "id": 2, "is_public": false }` |

Visibility updates do not change source, external ID, ownership, relationships, or achievement verification. They remain available for imported projects and records associated with verified achievements. Manual metadata restrictions still apply. The project row lock coordinates publication with Devpost import updates; a stale import preview may return HTTP 409 and can be retried after a new preview.

## Public privacy policy

- A project appears only when owned by the requested profile user and `is_public=True`. A project needs no public participation to appear.
- A participation appears only when owned by that user, `is_public=True`, and connected to an event owned by that user. Its event name, organizer, dates, format, URL, status, team name, and role may then appear.
- A submission appears only when its owner, project owner, event owner, and public participation belong to the requested user; the project must be public and the submission must be `submitted`. Draft and withdrawn submissions are omitted.
- An achievement appears only through a public participation. If linked to a submission, the linked project must also be public and the event and ownership relationships must match. Its stored verification status is shown unchanged. Evidence URLs are excluded.
- Summary counts use these same server-side predicates. Private records never contribute to the public Hackathon metrics. Import history, tokens, fingerprints, email, external IDs, administrative fields, and raw JSON are absent from the public Hackathon response.

## Public API

`GET /api/v1/profile/{username}/` retains `user`, `platforms`, and `competitive_programming` and adds:

```json
"hackathons": {
  "published_projects": 1,
  "public_participations": 1,
  "public_achievements": 2,
  "verified_achievements": 1
}
```

`GET /api/v1/profile/{username}/hackathons/` allows anonymous access. It returns `summary` with the same four counts and four paginated collections: `projects`, `participations`, `achievements`, and `submissions`. Each collection has `count`, `next`, `previous`, and `results`. Query parameters are `projects_page`, `participations_page`, `achievements_page`, `submissions_page`, and shared `page_size`; the default size is 12 and the maximum is 20. Collections order by newest creation time, then descending ID. Unknown users or out-of-range pages return 404. Empty portfolios return zero counts and empty result arrays.

Project results contain `id`, title, description, technologies, source, up to five recent eligible public event associations, and optional HTTP(S) project, repository, demo, video, and image URLs. Participation results contain `id`, status, team name, role, and a minimal nested public event. Achievement results contain `id`, participation ID, public linked project ID if any, type, title, rank, total participants, description, and actual verification status. Submission results contain `id`, public project and event IDs and names, and an optional HTTP(S) submission URL. The endpoint makes no Devpost request.

## Frontend workflow

The authenticated `/hackathon` project list shows `Private` or `Published` and offers an independent Publish/Remove action for manual and Devpost projects. The selected event detail offers the same control for participation, with a short explanation of what it exposes. Buttons disable while saving; the server response is awaited before refreshing existing dashboard data. The current page and selected event remain in place. Shared Axios authentication refresh and existing error handling remain in use.

The public `/profile/{username}` page adds real Hackathon counts to the domain card and a responsive portfolio section. Project cards show a fallback visual when no image is available, technologies, source, safe external links, and eligible submitted-work associations. Participation cards show public event and team details. Achievement cards label `verified`, `evidence_provided`, and `self_reported` distinctly. The section handles loading, retry, empty results, pagination, missing optional values, and profile changes without displaying a stale previous user's portfolio. CTF and Datathon cards retain their previous metrics.

## Files changed

| File | Purpose |
| --- | --- |
| `backend/apps/hackathons/views.py` | Owner-only visibility actions and row locks |
| `backend/apps/hackathons/test_visibility.py` | Authorization, import preference, verified context, and PostgreSQL race tests |
| `backend/apps/profiles/hackathon_public.py` | Public predicates, minimal serializers, summary, and pagination |
| `backend/apps/profiles/views.py`, `urls.py` | Profile summary and public portfolio endpoint |
| `backend/apps/profiles/test_hackathon_profile.py` | Anonymous access, privacy, pagination, deduplication, and query tests |
| `frontend/src/features/hackathons/api.ts` | Visibility API methods |
| `frontend/src/features/hackathons/components/visibility-control.tsx` | Shared publishing action |
| `frontend/src/features/hackathons/components/hackathon-page-content.tsx`, `hackathon-detail.tsx` | Project and participation controls |
| `frontend/src/features/profile/types.ts`, `api.ts`, `view-model.ts` | Public contracts, fetching, and real domain metrics |
| `frontend/src/features/profile/components/public-profile-page-content.tsx`, `domain-profile-cards.tsx` | Portfolio integration and domain card |
| `frontend/src/features/profile/components/hackathons/public-hackathon-portfolio.tsx` | Public cards, states, and pagination |
| `frontend/tests/public-hackathons.test.cjs` | Publishing and portfolio component tests |
| `README.md` | Public publishing entry point |

## Verification

Backend commands run from `backend` using `.venv\Scripts\python.exe`. Frontend commands run from `frontend`.

| Command | Result |
| --- | --- |
| `manage.py check` | PASS: no issues |
| `manage.py makemigrations --check --dry-run` | PASS: no changes |
| `manage.py migrate` | PASS: no migrations to apply |
| `manage.py test apps.hackathons -v 2` | PASS: 136 tests on PostgreSQL, including import/publication concurrency |
| `manage.py test apps.profiles -v 2` | PASS: 16 tests on PostgreSQL |
| `manage.py test apps.connectors -v 2` | PASS: 219 tests on PostgreSQL |
| `manage.py test` | PASS: 390 tests on PostgreSQL, after final code changes |
| `npm ci` | PASS outside sandbox; sandbox blocked npm lifecycle process |
| `npm run test:hackathons` | PASS: 16 tests |
| `npm run lint` | PASS |
| `npx tsc --noEmit` | PASS |
| `npm run build` | PASS with network access for existing Google fonts; sandbox fetch failed |
| Browser scenarios | BLOCKED: in-app browser initialization fails with `Cannot redefine property: process` before opening the app |

## Remaining limitations and acceptance

Project cards show at most five recent eligible public event associations; further associations remain available through the separately paginated Submitted work collection. URL validation accepts safe HTTP(S) links; the application does not verify that a linked external page is trustworthy or that a Devpost account is owned by the STALKER user. Publication is an explicit owner action and never grants verification.

Browser acceptance still needs an authenticated and anonymous run of the five scenarios below. The available in-app browser failed during initialization with `Cannot redefine property: process`, before it could open the local app. Once a working browser is available, start the backend with `backend\.venv\Scripts\python.exe backend\manage.py runserver` and frontend with `cd frontend; npm run dev`, then create two test users:

1. **Manual project:** As user A, create a project on `/hackathon`, confirm it starts Private, publish it, and open `/profile/{userA}` in an anonymous window. Confirm it appears. Unpublish and refresh the public page; confirm it disappears.
2. **Devpost project:** As user A, link a Devpost handle, preview and apply valid JSON, confirm its project starts Private, and publish it. Confirm it appears anonymously. Apply an updated import for the same project; confirm it stays Published and the imported title updates. Confirm the normal metadata editor remains disabled for that project.
3. **Participation:** As user A, create an event, participation, and project submission. Publish only the project; anonymously confirm the project appears without event or team details. Publish the participation and confirm the event and eligible submitted work appear. Hide the participation and confirm both disappear while the project remains.
4. **Achievement:** As user A, create a self-reported achievement on a private participation. Confirm it is absent anonymously. Publish the participation and confirm the badge reads Self-reported. If the achievement links to a private project, confirm that project and linked achievement remain hidden. Confirm the achievement verification status is unchanged after visibility actions.
5. **Cross-user:** As user B, try to change user A's project and participation visibility via the API and confirm each returns 404. As anonymous and authenticated user B, inspect `/api/v1/profile/{userA}/hackathons/` and confirm the same public results contain no private project, participation, event, submission, achievement, import token, or evidence data.

**PHASE 4 ACCEPTANCE PENDING** until every required check, including browser verification, has passed.

The next phase can build on these publication controls and privacy-filtered profile data; it should not infer verification from Devpost links or public visibility.
