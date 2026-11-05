# Hackathon portfolio management, discovery, and data quality

## Scope and existing architecture

This milestone extends the Phase 2 manual records, Phase 3 signed Devpost JSON import, and Phase 4 privacy controlled public portfolio. Django REST Framework remains the API layer; Next.js App Router remains the UI. It adds owner scoped discovery, project management details, a public project page, import change previews, and persistent review of possible manual/Devpost duplicates.

The Devpost importer still accepts user supplied JSON only. A review decision is **metadata about a pair, not a merge**. It never reassigns a submission or achievement, changes an imported external ID, publishes a record, or verifies a claim.

## API contracts

All management endpoints require authentication and scope records to the caller. Existing pagination uses `page` and `page_size` (maximum 100 for records). Invalid enum and overlong text filters return DRF HTTP 400 errors.

| Endpoint | Changes |
| --- | --- |
| `GET /api/v1/hackathons/projects/` | Adds `search` (case insensitive title or description), `source=manual\|devpost`, `visibility=public\|private`, `technology` (case insensitive exact JSON list member), and `ordering=newest\|oldest\|recently_updated\|title_asc\|title_desc`. Existing `title` remains available. Results include `related_hackathon_count`. |
| `GET /api/v1/hackathons/events/` | Keeps `name`, `status`, and `year`; adds `event_format=online\|in_person\|hybrid\|unknown`, `source=manual\|devpost`, and `ordering=newest\|oldest\|date_newest\|date_oldest\|name_asc`. `event_format` avoids DRF's reserved `format` renderer parameter. Missing dates sort last in either date order. |
| `GET /api/v1/profile/{username}/hackathons/projects/{project_id}/` | Anonymous public project detail. Returns `project`, `submission_count`, at most 20 eligible `submissions`, `achievement_count`, and at most 20 eligible `achievements`. Returns 404 for an unknown user, private or missing project, or wrong owner. |
| `POST /api/v1/hackathons/devpost/imports/preview/` | Adds `action_counts`, bounded per-field `changes` (`field`, `before`, `after`, `truncated`), reasons for protected/conflicting actions, and bounded manual candidate summaries. The existing signed preview/apply token contract remains authoritative. |
| `GET /api/v1/hackathons/duplicate-reviews/` | Returns at most 50 current URL based `candidates` and paginated owner-only saved `reviews` (default 20, maximum 50 per page). `page` and `page_size` paginate saved reviews. |
| `POST /api/v1/hackathons/duplicate-reviews/` | Body: `record_type` (`project` or `event`), integer `manual_id`, integer `imported_id`, `decision` (`unresolved`, `related`, `distinct`). A valid owner scoped manual/Devpost pair with a URL signal is required. Creates (201) or idempotently updates (200). |
| `PATCH /api/v1/hackathons/duplicate-reviews/{id}/` | Body: only `decision`. Owner only; repeated identical decisions leave `updated_at` unchanged. |

All sorts use explicit allowlists and primary key tie breakers. Search and technology strings are limited to 100 characters. Technology membership uses parameterized PostgreSQL `jsonb_array_elements_text` or SQLite `json_each`; arbitrary user input is never interpolated into SQL or ordering. The related Hackathon count uses a correlated aggregate, so the project list does not fetch submissions for each card.

## Public privacy and detail page

The detail API reuses Phase 4's public project, submission, and achievement query predicates. Project publication is independent of participation publication. A private participation cannot become public just because its project is public; likewise a published participation does not reveal a private project. Hidden relationships, private evidence, import history, raw JSON, fingerprints, and review decisions are excluded. Related collections are limited to the latest 20 eligible rows and include total eligible counts.

The public profile links project titles to `/profile/{username}/hackathons/projects/{projectId}`. The page renders a fallback image, technologies, source, safe external links, eligible work and achievements, plus loading, 404, and network error states. The existing independently paginated portfolio collections remain intact. Devpost and DoraHacks accounts now appear in the public Hackathon platform view without entering competitive programming totals. Both private and public achievement views share the verified / evidence provided / self reported label mapping.

## Import preview and review decisions

The inspector compares import managed fields of already imported projects, events, and submissions in memory against normalized incoming rows. Only authorized, bounded before/after values are returned; long strings and technology lists are truncated. Preview remains read only. Apply still uses the signed token, state fingerprint, ownership checks, transaction, stable imported identity, publication preference, and verified achievement protections. A stale preview must be regenerated. Candidate summaries remain suggestions.

`HackathonDuplicateReview` stores owner, record type, one manual FK, one Devpost FK, decision, and timestamps. Migration `0005_hackathonduplicatereview` adds a type-shape check, conditional unique constraints for project/event pairs, and an owner/update index. Deleting either record cascades to its review metadata; it does not change the surviving record. The API validates ownership, source, distinctness, and a matching URL signal under a transaction. PostgreSQL user and record row locks serialize concurrent review writes; database uniqueness is a final backstop. Saved decisions can be changed or left unresolved. Decisions do not influence import matching, verification, or public serialization.

Candidate discovery examines at most 50 recent imported records and 250 matching or recent manual records per type and returns at most 50 suggestions. Host case, HTTP/HTTPS, and trailing slashes are normalized. URL paths and query strings remain distinct. Older pairs outside the search window can still be reviewed if they have a valid URL signal, but may not be suggested automatically.

## Frontend changes

The authenticated dashboard has controlled project and event filters, counts, clear empty states, pagination reset, request ordering guards, and retained last valid data on transient failures. Project cards show description, technology, source, publication state, links, update date, and related Hackathon count while preserving manual/imported edit restrictions and visibility controls. Devpost preview shows action counts, field changes, reasons, and candidates without displaying its token. A separate review panel shows both records and lets users mark a pair related, distinct, or unresolved without a merge action.

## Tests and integrity considerations

Backend regressions cover combined owner scoped filters, stable sorting and pagination, SQLite/PostgreSQL technology membership, public detail privacy and query bounds, read only import diffs and stale tokens, review authorization and invariants, and PostgreSQL concurrent duplicate decisions. Existing Hackathon, profile, and connector suites cover prior import, verification, publishing, and ownership behavior. Frontend tests cover verification labels, platform accounts, filters, stale responses, management cards, preview details, review decisions, public project states, and existing publishing behavior.

The review model's database constraints enforce pair shape and uniqueness, while the API checks ownership and source under locks. There is no global duplicate merge. SQLite does not provide PostgreSQL's row locking semantics, so its tests establish functional compatibility only; the concurrency case is skipped on SQLite and run against PostgreSQL.

## Validation and acceptance

The following results are from the local environment on 2026-11-05. Backend checks use the configured PostgreSQL database unless noted.

| Check | Result | Detail |
| --- | --- | --- |
| `python manage.py check` | PASS | No system check issues. |
| `python manage.py makemigrations --check --dry-run` | PASS | No changes detected. |
| `python manage.py migrate` | PASS | Applied migration 0005. |
| Focused PostgreSQL backend regressions | PASS | 10 tests. |
| Focused SQLite backend regressions | PASS | 10 tests, 1 PostgreSQL concurrency skip. |
| `python manage.py test apps.hackathons -v 2` | PASS | 146 tests, including PostgreSQL concurrency. |
| `python manage.py test apps.profiles -v 2` | PASS | 19 tests. |
| `python manage.py test apps.connectors -v 2` | PASS | 219 tests. |
| `python manage.py test` | PASS | 403 tests against PostgreSQL. |
| `npm ci` | PASS | 481 packages installed; audit reported 22 dependency advisories. |
| `npm run test:hackathons` | PASS | 24 tests. |
| `npm run lint` | PASS | No warnings. |
| `npx tsc --noEmit` | PASS | No errors. |
| `npm run build` | PASS | New dynamic route built. |
| Browser acceptance | BLOCKED | In-app browser bootstrap failed with `Cannot redefine property: process`. |

Browser scenarios 1–7 in the Phase 5 brief remain unverified. To reproduce them, start the backend and frontend with test accounts and representative manual/imported records, then exercise the project filters and pagination, event filters and manual editing, anonymous project publish/unpublish visibility, signed Devpost preview/apply/reimport, duplicate decision changes, cross-user authorization, and Phase 4 public publishing/privacy flows. Confirm the expected API status codes and visible UI states at each step. Unit tests do not substitute for this browser pass.

**Acceptance decision: HACKATHON PORTFOLIO MANAGEMENT ACCEPTANCE PENDING.** Browser acceptance remains blocked. This milestone should undergo independent review and the seven browser scenarios before acceptance.

## Known limitations and next milestone

Suggestion discovery is intentionally bounded and URL based; it does not identify all possible real world duplicates. Public detail returns the latest 20 eligible associations of each type, with total counts; pagination of these nested collections can be added if needed. Dependency audit advisories should be reviewed separately before deployment. The next milestone should begin only after browser acceptance and independent review; this work does not implement automatic synchronization, verification, or destructive merging.

Recommended commit subjects, split by concern: `fix(profile): show hackathon accounts and verification labels`, `feat(hackathons): add portfolio discovery filters`, `feat(profiles): add public hackathon project detail`, `feat(hackathons): add import diffs and duplicate reviews`, and `docs(hackathons): document portfolio management`.
