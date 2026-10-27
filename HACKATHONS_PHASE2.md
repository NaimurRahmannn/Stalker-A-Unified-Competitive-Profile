# Hackathons Phase 2: manual management

All paths below are relative to `/api/v1/hackathons/`. Every endpoint requires a JWT bearer token. Lists use DRF page-number pagination (20 records by default, `page_size` up to 100) and return `{ "count": 1, "next": null, "previous": null, "results": [...] }`. Foreign-key IDs are resolved only inside the authenticated user's records. Missing and other users' detail IDs return 404. Invalid writes return 400 with field errors. The overview path and its Phase 1 count meanings are unchanged.

| Path | Methods | Writable fields |
| --- | --- | --- |
| `overview/` | GET | None. Returns `hackathons_attended`, `projects_submitted`, `achievements_recorded`, `placements_recorded`. |
| `events/`, `events/{id}/` | GET list or detail, POST, PATCH, DELETE | `name`, `organizer`, `description`, `event_url`, `start_date`, `end_date`, `format` (`online`, `in_person`, `hybrid`, `unknown`). Filters: `status`, `year`. |
| `projects/`, `projects/{id}/` | GET list or detail, POST, PATCH, DELETE | `title`, `description`, `repository_url`, `demo_url`, `video_url`, `image_url`, `technologies` (string array), `is_public`. Filter: `title`. |
| `participations/`, `participations/{id}/` | GET list or detail, POST, PATCH, DELETE | `event` on create only; `status` (`registered`, `attended`, `submitted`), `team_name`, `role`, `is_public`. |
| `submissions/`, `submissions/{id}/` | GET list or detail, POST, PATCH, DELETE | `event` and `project` on create only; `status` (`draft`, `submitted`, `withdrawn`), `submission_url`, `submitted_at` (ISO 8601). |
| `achievements/`, `achievements/{id}/` | GET list or detail, POST, PATCH, DELETE | `participation` on create only; `submission` (nullable), `achievement_type` (`placement`, `award`, `finalist`, `participation`, `other`), `title`, `rank`, `total_participants`, `description`, `evidence_url`. Filter: `achievement_type`. |
| `entries/` | POST | Composite request described below. |

POST returns the created record with HTTP 201. PATCH returns the updated record with HTTP 200. DELETE returns HTTP 204. Event responses also contain the user's `participation`, `submissions`, and `achievements`. Optional URL fields accept HTTP(S) URLs or empty strings. Optional dates and numeric values accept `null`. Rank and total participants must be positive, and rank cannot exceed total participants. `source`, `external_id`, ownership fields, `verification_status`, and timestamps cannot be supplied. Immutable relationship fields cannot be patched. New projects and participations remain private by default; visibility changes require an explicit PATCH.

Imported events, projects, and submissions are visible to their owner but are read-only through these manual endpoints. Their deletion is blocked. Deletion of a manual event or project is also blocked when it would cascade to an imported submission. User-created achievements under imported participations remain editable. Deleting an event cascades to its participation, submissions, and achievements. Deleting a project cascades to its submissions; linked achievements retain their participation and lose the submission link. Deleting a participation cascades to its achievements.

## Composite entry

`POST entries/` requires exactly one of `event` or `event_id`, and a `participation` object. It accepts either `project` or `project_id`, plus a `submission` object when a project is provided. `achievements` is optional. A new event creates a new participation. For an explicitly selected existing event, an existing participation is reused only if the supplied participation fields match; pass `{}` to reuse it without edits. Use the participation PATCH endpoint to change status or team details. A project may be reused across events, while one project/event pair may have only one submission. `link_submission: true` on an achievement links it to the submission created in the same request. Submission and participation statuses are independent and never automatically changed to match each other.

Minimal entry:

```json
{
  "event": { "name": "Community Hack Day", "format": "online" },
  "participation": { "status": "registered" }
}
```

Reuse an owned project with two achievements:

```json
{
  "event": { "name": "AI Challenge", "start_date": "2026-11-10" },
  "participation": { "status": "submitted", "team_name": "Team Nova" },
  "project_id": 42,
  "submission": { "status": "submitted", "submission_url": "https://example.com/entry" },
  "achievements": [
    { "achievement_type": "placement", "title": "First Runner-Up", "rank": 2, "total_participants": 150, "link_submission": true },
    { "achievement_type": "award", "title": "Best AI Project" }
  ]
}
```

On success, HTTP 201 returns:

```json
{ "event_id": 12, "participation_id": 8, "project_id": 42, "submission_id": 15, "achievement_ids": [21, 22] }
```

The whole operation runs inside one database transaction. Validation or uniqueness failures return HTTP 400 and roll back every new record. Database constraints continue to prevent duplicate participations and project/event submissions under concurrent requests.
