# Phase 3: Devpost integration

## Scope and access

This phase links a Devpost reference and imports a user-provided structured JSON document. The JSON format belongs to **STALKER**; it is **not** an official Devpost API or export format. Devpost does not provide a confirmed public portfolio import API for this feature, and its published terms prohibit automated scraping or crawling. STALKER does not fetch, scrape, or validate URLs against Devpost. An entered link or successful import does not establish account ownership or verify an achievement. Automatic Devpost synchronization remains disabled.

The import is synchronous and bounded. Phase 4 may add an authorized acquisition provider only after access rights, format, authentication, rate limits, and operations have been reviewed. No provider token, password, or session cookie is accepted or stored here.

Phase 3 is implemented for independent review; it is not independently accepted here.

## Architecture

- **Identity:** The existing `PlatformAccount` row with `platform="devpost"` holds one canonical lowercase handle and `https://devpost.com/{handle}` URL per STALKER user. `is_verified` is the historical handle-validity flag. Linking sets neither it nor `ownership_verified_at`. Changing the handle resets prior verification and sync state through the existing serializer update path; unlinking deletes the account row but leaves Hackathon records and import history.
- **Acquisition:** `UserJsonProvider` accepts only a structured object. `StructuredDataProvider` documents the seam for a future officially authorized API or export. No network provider is registered.
- **Validation and normalization:** `schema.py` checks format version, allowed fields, required values, dates, URL structure, and size limits before creating typed project/event/submission records. `identity.py` derives canonical HTTPS Devpost references and SHA-256 external IDs from the linked handle and source references. Repository and demo URLs are stored as data only.
- **Preview:** `inspect_import` reads owner-scoped records and reports creates, updates, unchanged records, protected skips, conflicts, and possible manual URL matches. It writes no Hackathon record or completed history run. It signs a token bound to user, linked account ID and update timestamp, canonical document digest, and a fingerprint of relevant database state. Tokens expire after 15 minutes.
- **Apply:** A transaction locks the linked account, relevant imported parents and children, and dependent achievements before rechecking the signed state. It creates or updates only owner-scoped `source="devpost"` core records and creates one owner-scoped participation for each explicitly referenced event when none exists. An explicit submitted relationship starts that new participation as `submitted`; other relationships start it as `registered`. Existing participation details are never overwritten. Verified context is skipped. Identity and project/event uniqueness constraints remain the database backstop. A retry with the same completed preview returns the same import run. A changed account or changed relevant data requires a new preview. Database conflicts roll back the whole project graph and become HTTP 409 without SQL details.
- **Provenance:** `DevpostImportRun` stores the input method (`user_json`), linked handle, summary counts, a request fingerprint, result IDs and warnings, and timestamps. The linked account FK is nullable so unlinking preserves history. Imported core records retain `source="devpost"`, canonical `project_url` where applicable, and stable `external_id`. Raw uploaded JSON is not stored.

## STALKER JSON v1

See [the sample file](examples/devpost_import_v1.json). The top-level object must have `format_version: 1`, a `profile_url` matching the linked handle, and a `projects` array. Each project needs a Devpost `/software/{slug}` URL and title. Optional fields are `description`, `repository_url`, `demo_url`, `technologies`, and `submissions`. A project with no submissions stays a portfolio-only project. Each submission needs a name, stable Devpost hackathon subdomain URL, and explicit `draft`, `submitted`, or `withdrawn` status. Optional fields are organizer, start/end dates in `YYYY-MM-DD`, event format (`online`, `in_person`, `hybrid`, `unknown`), and submission URL. Unknown fields, including `owner`, internal IDs, verification status, awards, and ranks, are rejected.

Limits: **1 MB per request**, **100 projects**, **20 submissions per project**, **30 technologies per project**; titles and URLs are capped to their model limits. Event URLs must be root URLs of a Devpost hackathon subdomain such as `https://global-ai-hackathon.devpost.com/`. Event dates and organizer are never invented. Projects without a referenced event do not create submissions, participations, awards, placements, or ratings.

## API

All paths below are under `/api/v1/` and require authentication. The frontend uses the existing Axios client and auth tokens.

| Method and path | Request | Response |
| --- | --- | --- |
| `POST platform-accounts/` | `{ "platform": "devpost", "handle": "example_user" }` or a Devpost profile URL in `handle` | Canonical account, including separate `ownership_verified` flag |
| `PATCH platform-accounts/{id}/` | `{ "handle": "new_user" }` | Updated canonical account; prior previews invalidated |
| `DELETE platform-accounts/{id}/` | None | 204; historical imports remain |
| `POST hackathons/devpost/imports/preview/` | STALKER JSON v1 document | Counts, per-record actions, possible manual matches, conflicts, signed `preview_token` |
| `POST hackathons/devpost/imports/` | `{ "document": <same JSON>, "preview_token": "..." }` | Import run and summary counts; same-token retries return same run |
| `GET hackathons/devpost/imports/?page=1` | None | Paginated owner-only history, 20 per page |
| `GET hackathons/devpost/imports/{id}/` | None | Owner-only import result |

Error codes: **400** malformed or unsupported input, **401** unauthenticated, **403** another user's preview token, **404** missing linked account or inaccessible run, **409** expired/stale preview or identity conflict, **413** oversized request. Error details avoid internal SQL. The generic `platform-accounts/{id}/sync/` still reports Devpost sync as unsupported.

## Frontend workflow

The existing `/hackathon` page keeps the Phase 2 manual forms, overview, lists, editing, and deletion. Its Devpost section links, changes, or unlinks the existing platform account and labels ownership verification separately. A handle change warns that pending previews become invalid and historical records remain. Users can paste JSON, select a `.json` file, or load the STALKER schema example. Preview shows record actions and possible manual matches; an explicit checkbox is required before apply. Result counts and warnings appear after apply, and the existing lists and overview refresh. Owner-scoped import history is paginated. Imported events and projects are labeled as imports; imported projects link to their canonical Devpost URL and remain read-only through manual CRUD.

## Identity, deduplication, and manual data

Project identity is derived from the linked handle and canonical Devpost project URL. Event identity uses the linked handle and canonical Devpost hackathon subdomain URL. Submission identity uses the handle, project URL, and event URL, so one project may belong to multiple events. No client-supplied external ID is trusted. Different STALKER users receive separate local rows. Existing database constraints enforce owner/source/external identity and one submission per project/event.

After a handle change, previously imported records retain their original attribution. If the newly linked handle supplies a project or event URL already imported under the old identity, preview reports a conflict and apply returns 409. This prevents silent cross-handle duplication; an administrator can review genuine identity changes separately.

Manual records are never rewritten or converted. Preview reports potential manual matches by available project, repository, demo, or event URLs; the import defaults to retaining separate records. A verified achievement is never created, moved, edited, or deleted by import. Changes to imported event, project, or submission context used by a verified achievement are skipped with a warning. Ordinary manual CRUD continues to treat imported core records as read-only. Users may add a self-reported achievement through the existing achievement API to the imported event's participation.

## Migration, testing, and limitations

Migration `hackathons.0004` adds a nullable `HackathonProject.project_url` for imported source provenance and the indexed, owner-scoped `DevpostImportRun` history model. Migrations 0001–0003 and existing manual data are unchanged. Apply migrations with `python manage.py migrate`.

Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `python manage.py migrate`, `python manage.py test apps.hackathons -v 2`, `python manage.py test apps.connectors -v 2`, and `python manage.py test` from `backend`. Run `npm run lint`, `npx tsc --noEmit`, and `npm run build` from `frontend`. PostgreSQL runs the row-lock `TransactionTestCase` tests; SQLite does not support `SELECT FOR UPDATE`, so SQLite results cannot establish concurrency ordering.

Current limits: no automatic Devpost acquisition, no ownership verification workflow, no merge of manual and imported records, no background jobs, and no large-batch import. Import history preserves counts and IDs rather than raw uploaded documents. These are potential Phase 4 integration points, subject to separate authorization and design review.
