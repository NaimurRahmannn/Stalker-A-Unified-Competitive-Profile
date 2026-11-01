# Phase 3.1: Devpost import stabilization

## Objectives and findings

Phase 3.1 stabilizes the user-supplied Devpost JSON workflow and verifies the Phase 2 manual Hackathon behavior. Preview and apply previously shared a 1 MiB raw HTTP limit even though apply wraps the document with a signed token. A document near the limit could preview successfully and fail at apply. The browser example used plausible project and event data that could be imported accidentally. Apply also searched every planned submission for each event action.

## Changes

- The importer now measures the compact UTF-8 JSON document separately from the request. Both endpoints enforce a 1,048,576-byte document limit and a 1,064,960-byte raw request limit, leaving 16 KiB for formatting and the apply envelope. Apply tokens are capped at 8,192 characters. Oversized documents and requests return structured HTTP 413 responses. Per-field length checks reject oversized whitespace-padded values before trimming. Signed token, account, owner, and stale-state checks remain in place.
- Event actions are indexed once before apply processes events. The importer retains the existing event and project order, transaction boundaries, and database query pattern.
- The in-page schema example and repository sample now use obvious placeholders and draft status. The frontend blocks preview while any of these placeholders remain, explains that the data is demonstrative, and checks the canonical document size before sending it. The explicit confirmation checkbox remains required for apply.
- Devpost component tests use a local DOM and mocked service calls, with the real validation schema and API error parser. They do not call Devpost or any live API.

## Modified files

| File | Purpose |
| --- | --- |
| `backend/apps/hackathons/services/devpost/schema.py` | Canonical document limit, envelope limit, and strict raw field lengths |
| `backend/apps/hackathons/devpost_views.py` | Bounded HTTP requests and token length |
| `backend/apps/hackathons/services/devpost/import_service.py` | Indexed event actions during apply |
| `backend/apps/hackathons/test_devpost.py` | Boundary, malformed-input, token, and upper-bound regression cases |
| `frontend/src/features/hackathons/devpost-example.ts` | Placeholder example, guard, and client size constants |
| `frontend/src/features/hackathons/components/devpost-integration.tsx` | Safer example flow and matching size checks |
| `frontend/tests/devpost.test.cjs` | Devpost component interactions and error states |
| `frontend/package.json`, `frontend/package-lock.json` | DOM test dependency and test command |
| `examples/devpost_import_v1.json` | Demonstration placeholders |
| `HACKATHONS_PHASE3.md` | Updated size contract and example workflow |

No migrations or new verification workflow were introduced. Imported identity and verified-achievement protection remain unchanged.

## Tests added and retained

Backend tests cover one byte below, exactly at, and one byte above the canonical document limit; near-limit apply with the signed token; raw request overflow on both endpoints; oversized token; malformed and non-JSON requests; missing required fields; whitespace-padded field lengths; tampered tokens; and a 100-project, 2,000-submission preview with a query ceiling. The exact-limit apply creates 100 projects and 100 submissions on PostgreSQL. Existing tests cover stale and expired tokens, cross-user scope, protected achievements, rollback, uniqueness, idempotence, and concurrent apply. The Phase 2 suite covers manual CRUD, relationships, deletion and update protections, and overview statistics.

Frontend tests cover linking, changing, and unlinking a Devpost profile; file selection; invalid JSON and schema; oversized files; preview and confirmation; successful apply and refresh; history pagination; loading states and repeated-request prevention; HTTP 403, 409, 413, and 500 errors for preview and apply; and the example guard. The existing manual form tests include timezone round trips.

## Verification

Backend commands were run from `backend` with `.venv\Scripts\python.exe`; frontend commands were run from `frontend`.

| Command or check | Result |
| --- | --- |
| Backend `manage.py check` | PASS — no issues |
| Backend `manage.py makemigrations --check --dry-run` | PASS — no changes detected |
| Backend `manage.py migrate` | PASS — no migrations to apply |
| Backend `manage.py test apps.hackathons -v 2` | PASS — 131 tests on PostgreSQL, including concurrency |
| Backend `manage.py test apps.connectors -v 2` | PASS — 219 tests on PostgreSQL |
| Backend `manage.py test` | PASS — 380 tests on PostgreSQL |
| Frontend `npm ci` | PASS |
| Frontend `npm run test:hackathons` | PASS — 11 tests |
| Frontend `npm run lint` | PASS |
| Frontend `npx tsc --noEmit` | PASS |
| Frontend `npm run build` | PASS with network access; sandboxed build could not fetch configured Google fonts |
| Browser end-to-end workflow | BLOCKED — in-app browser initialization fails with `Cannot redefine property: process` |

## Remaining risks and acceptance

The browser end-to-end check remains blocked by the available browser integration. The DOM tests and PostgreSQL API tests exercise the component and service separately, but do not replace a real authenticated browser run. To finish, start the backend with `backend\.venv\Scripts\python.exe backend\manage.py runserver` and the frontend with `cd frontend; npm run dev`, sign in with a test account, then exercise link → preview → apply → history and the manual Phase 2 create/edit flows in a working browser. The dependency install also reported 29 npm audit advisories; dependency upgrades were outside this targeted change.

**Phase 3 ACCEPTANCE PENDING** because the browser workflow is blocked. The Phase 4 integration surface is the owner-scoped Devpost account link, JSON preview/apply/history endpoints, and the `/hackathon` page's Devpost section. Phase 4 implementation has not begun.
