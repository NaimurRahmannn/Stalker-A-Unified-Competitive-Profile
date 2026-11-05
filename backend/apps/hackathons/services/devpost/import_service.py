"""Preview, confirmation, and transactional persistence for structured imports."""

from dataclasses import asdict
import hashlib
import json

from django.core import signing
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied

from apps.connectors.models import PlatformAccount
from apps.hackathons.models import (
    DevpostImportRun, HackathonAchievement, HackathonEvent,
    HackathonParticipation, HackathonProject, HackathonSubmission,
)
from .schema import NormalizedDocument


TOKEN_SALT = "hackathons.devpost.preview.v1"
TOKEN_AGE = 900


class ImportConflict(APIException):
    status_code = 409
    default_detail = "The import preview is stale or conflicts with current records. Preview again."
    default_code = "import_conflict"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _locked(queryset, lock):
    return queryset.select_for_update() if lock else queryset


def _preview_value(value):
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    if isinstance(value, str):
        return value[:240], len(value) > 240
    if isinstance(value, (tuple, list)):
        return [item[:100] if isinstance(item, str) else item for item in value[:30]], len(value) > 30 or any(
            isinstance(item, str) and len(item) > 100 for item in value[:30]
        )
    return value, False


def _field_changes(current, incoming, fields):
    if current is None:
        return []
    changes = []
    for field in fields:
        before = getattr(current, field)
        after = getattr(incoming, field)
        if field == "technologies":
            after = list(after)
        if before != after:
            shown_before, before_cut = _preview_value(before)
            shown_after, after_cut = _preview_value(after)
            changes.append({"field": field, "before": shown_before, "after": shown_after,
                            "truncated": before_cut or after_cut})
    return changes


def inspect_import(user, document: NormalizedDocument, lock=False):
    """Return a plan and its current-state fingerprint; never write records."""
    events = {submission.event.external_id: submission.event for project in document.projects for submission in project.submissions}
    project_ids = [project.external_id for project in document.projects]
    project_urls = [project.project_url for project in document.projects]
    event_urls = [event.event_url for event in events.values()]
    submission_ids = [submission.external_id for project in document.projects for submission in project.submissions]
    existing_events = list(_locked(HackathonEvent.objects.filter(owner=user, source="devpost").filter(
        Q(external_id__in=events) | Q(event_url__in=event_urls)
    ).order_by("pk"), lock))
    event_by_external = {obj.external_id: obj for obj in existing_events}
    event_ids_by_url = {}
    for obj in existing_events:
        if obj.event_url:
            event_ids_by_url.setdefault(obj.event_url, set()).add(obj.external_id)
    event_pks = [obj.pk for obj in existing_events]
    participation_query = HackathonParticipation.objects.filter(user=user, event_id__in=event_pks).order_by("pk")
    existing_participations = list(_locked(participation_query, lock))
    participation_by_event = {obj.event_id: obj for obj in existing_participations}
    existing_projects = list(_locked(HackathonProject.objects.filter(owner=user, source="devpost").filter(
        Q(external_id__in=project_ids) | Q(project_url__in=project_urls)
    ).order_by("pk"), lock))
    project_by_external = {obj.external_id: obj for obj in existing_projects}
    project_ids_by_url = {}
    for obj in existing_projects:
        if obj.project_url:
            project_ids_by_url.setdefault(obj.project_url, set()).add(obj.external_id)
    project_pks = [obj.pk for obj in existing_projects]
    relevant_submissions = list(_locked(HackathonSubmission.objects.filter(owner=user).filter(
        Q(source="devpost", external_id__in=submission_ids) | Q(event_id__in=event_pks) | Q(project_id__in=project_pks)
    ).order_by("pk"), lock))
    submission_by_external = {obj.external_id: obj for obj in relevant_submissions if obj.source == "devpost"}
    submission_by_pair = {(obj.project_id, obj.event_id): obj for obj in relevant_submissions}
    submission_pks = [obj.pk for obj in relevant_submissions]
    achievement_query = HackathonAchievement.objects.filter(
        Q(participation__event_id__in=event_pks) |
        Q(submission__project_id__in=project_pks) |
        Q(submission_id__in=submission_pks)
    ).order_by("pk")
    if lock:
        achievement_query = achievement_query.select_for_update(of=("self",))
    achievement_rows = list(achievement_query.values_list(
        "pk", "participation__event_id", "submission__project_id", "submission_id", "verification_status", "updated_at"
    ))
    verified = HackathonAchievement.VerificationStatus.VERIFIED
    protected_events = {row[1] for row in achievement_rows if row[4] == verified}
    protected_projects = {row[2] for row in achievement_rows if row[4] == verified and row[2] is not None}
    protected_submissions = {row[3] for row in achievement_rows if row[4] == verified and row[3] is not None}

    manual_event_urls = {
        prefix + url.removeprefix("https://").rstrip("/") + suffix
        for url in event_urls for prefix in ("http://", "https://") for suffix in ("", "/")
    }
    manual_events = list(HackathonEvent.objects.filter(owner=user, source="manual", event_url__in=manual_event_urls)
                         .order_by("pk").values("id", "name", "event_url", "updated_at")[:500])
    repo_urls = [project.repository_url for project in document.projects if project.repository_url]
    demo_urls = [project.demo_url for project in document.projects if project.demo_url]
    manual_projects = list(HackathonProject.objects.filter(owner=user, source="manual").filter(
        Q(project_url__in=project_urls) | Q(repository_url__in=repo_urls + project_urls) | Q(demo_url__in=demo_urls + project_urls)
    ).order_by("pk").values("id", "title", "project_url", "repository_url", "demo_url", "updated_at")[:500])

    event_actions = {}
    event_changes = {}
    participation_actions = {}
    conflicts = []
    for key, incoming in events.items():
        current = event_by_external.get(key)
        event_changes[key] = _field_changes(current, incoming, ("name", "event_url", "organizer", "start_date", "end_date", "format"))
        if event_ids_by_url.get(incoming.event_url, set()) - {key}:
            action = "conflict"
            conflicts.append({"project_url": "", "event_url": incoming.event_url})
        elif current is None:
            action = "create"
        else:
            changed = any((getattr(current, field) != getattr(incoming, field)) for field in (
                "name", "event_url", "organizer", "start_date", "end_date", "format"
            ))
            action = "protected" if changed and current.pk in protected_events else "update" if changed else "unchanged"
        event_actions[key] = action
        participation_actions[key] = "conflict" if action == "conflict" else "unchanged" if current and current.pk in participation_by_event else "create"

    project_actions = {}
    project_changes = {}
    for incoming in document.projects:
        current = project_by_external.get(incoming.external_id)
        project_changes[incoming.external_id] = _field_changes(current, incoming,
            ("title", "project_url", "description", "repository_url", "demo_url", "technologies"))
        if project_ids_by_url.get(incoming.project_url, set()) - {incoming.external_id}:
            action = "conflict"
            conflicts.append({"project_url": incoming.project_url, "event_url": ""})
        elif current is None:
            action = "create"
        else:
            changed = (current.title != incoming.title or current.project_url != incoming.project_url or current.description != incoming.description or
                       current.repository_url != incoming.repository_url or current.demo_url != incoming.demo_url or
                       current.technologies != list(incoming.technologies))
            action = "protected" if changed and current.pk in protected_projects else "update" if changed else "unchanged"
        project_actions[incoming.external_id] = action

    submission_actions = {}
    submission_changes = {}
    for project in document.projects:
        for incoming in project.submissions:
            current = submission_by_external.get(incoming.external_id)
            submission_changes[incoming.external_id] = _field_changes(current, incoming, ("status", "submission_url"))
            existing_project = project_by_external.get(project.external_id)
            existing_event = event_by_external.get(incoming.event.external_id)
            pair = (existing_project.pk, existing_event.pk) if existing_project and existing_event else None
            pair_record = submission_by_pair.get(pair) if pair else None
            if project_actions[project.external_id] == "conflict" or event_actions[incoming.event.external_id] == "conflict":
                action = "conflict"
            elif current and (current.project_id != (existing_project.pk if existing_project else None) or
                            current.event_id != (existing_event.pk if existing_event else None)):
                action = "conflict"
            elif pair_record and (pair_record.source != "devpost" or pair_record.external_id != incoming.external_id):
                action = "conflict"
            elif current is None:
                action = "create"
            else:
                changed = current.status != incoming.status or current.submission_url != incoming.submission_url
                action = "protected" if changed and current.pk in protected_submissions else "update" if changed else "unchanged"
            submission_actions[incoming.external_id] = action
            if action == "conflict":
                conflicts.append({"project_url": project.project_url, "event_url": incoming.event.event_url})

    projects_public = []
    for project in document.projects:
        matches = [row for row in manual_projects if
                   row["project_url"] == project.project_url or
                   project.repository_url and row["repository_url"] == project.repository_url or
                   project.demo_url and row["demo_url"] == project.demo_url or
                   row["repository_url"] == project.project_url or row["demo_url"] == project.project_url]
        matches = matches[:5]
        projects_public.append({
            "project_url": project.project_url, "title": project.title,
            "action": project_actions[project.external_id], "changes": project_changes[project.external_id],
            "reason": "A verified achievement protects this record." if project_actions[project.external_id] == "protected" else
                      "An imported source identity conflicts with an existing record." if project_actions[project.external_id] == "conflict" else "",
            "possible_manual_project_ids": [row["id"] for row in matches],
            "possible_manual_projects": [{"id": row["id"], "title": row["title"],
                "project_url": row["project_url"], "repository_url": row["repository_url"],
                "demo_url": row["demo_url"], "reason": "Matching project or repository or demo URL"} for row in matches],
            "submissions": [{
                "event_url": submission.event.event_url,
                "event_name": submission.event.name,
                "event_action": event_actions[submission.event.external_id],
                "event_reason": "A verified achievement protects this event." if event_actions[submission.event.external_id] == "protected" else
                                "An imported event identity conflicts with an existing record." if event_actions[submission.event.external_id] == "conflict" else "",
                "event_changes": event_changes[submission.event.external_id],
                "participation_action": participation_actions[submission.event.external_id],
                "action": submission_actions[submission.external_id],
                "changes": submission_changes[submission.external_id],
                "reason": "A verified achievement protects this submission." if submission_actions[submission.external_id] == "protected" else
                          "The submission identity or project/event pair conflicts with an existing record." if submission_actions[submission.external_id] == "conflict" else "",
                "possible_manual_event_ids": [row["id"] for row in manual_events if row["event_url"].removeprefix("http://").removeprefix("https://").rstrip("/") == submission.event.event_url.removeprefix("https://").rstrip("/")][:5],
                "possible_manual_events": [{"id": row["id"], "name": row["name"], "event_url": row["event_url"],
                    "reason": "Matching event URL"} for row in manual_events if row["event_url"].removeprefix("http://").removeprefix("https://").rstrip("/") == submission.event.event_url.removeprefix("https://").rstrip("/")][:5],
            } for submission in project.submissions],
        })
    all_actions = (*event_actions.values(), *participation_actions.values(), *project_actions.values(), *submission_actions.values())
    public = {
        "projects_detected": len(document.projects),
        "hackathons_detected": len(events),
        "submissions_detected": len(submission_ids),
        "participations_detected": len(events),
        "new_records": sum(action == "create" for action in all_actions),
        "existing_matches": sum(action in {"update", "unchanged", "protected"} for action in all_actions),
        "protected_records": sum(action == "protected" for action in (*event_actions.values(), *project_actions.values(), *submission_actions.values())),
        "action_counts": {action: sum(item == action for item in all_actions) for action in ("create", "update", "unchanged", "protected", "conflict")},
        "potential_manual_duplicates": len(manual_events) + len(manual_projects),
        "conflicts": conflicts,
        "projects": projects_public,
    }
    state = {
        "events": [(obj.pk, obj.external_id, obj.name, obj.organizer, obj.event_url, obj.start_date, obj.end_date, obj.format, obj.updated_at) for obj in existing_events],
        "participations": [(obj.pk, obj.event_id, obj.status, obj.updated_at) for obj in existing_participations],
        "projects": [(obj.pk, obj.external_id, obj.title, obj.project_url, obj.description, obj.repository_url, obj.demo_url, obj.technologies, obj.updated_at) for obj in existing_projects],
        "submissions": [(obj.pk, obj.external_id, obj.project_id, obj.event_id, obj.status, obj.submission_url, obj.updated_at) for obj in relevant_submissions],
        "achievements": achievement_rows,
        "manual_events": manual_events,
        "manual_projects": manual_projects,
    }
    return public, _digest(state), event_by_external, project_by_external, submission_by_external


def preview(user, account, document: NormalizedDocument):
    public, state, *_ = inspect_import(user, document)
    payload = {
        "user": user.pk, "account": account.pk, "account_updated_at": account.updated_at.isoformat(),
        "handle": account.handle, "document": _digest(asdict(document)), "state": state,
    }
    return {**public, "preview_token": signing.dumps(payload, salt=TOKEN_SALT, compress=True), "expires_in_seconds": TOKEN_AGE}


def apply_import(user, account_id: int, document: NormalizedDocument, token: str):
    try:
        signed = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_AGE)
    except (signing.BadSignature, signing.SignatureExpired) as exc:
        raise ImportConflict("Preview confirmation is invalid or expired. Preview again.") from exc
    if signed.get("user") != user.pk:
        raise PermissionDenied("This preview belongs to another user.")
    if signed.get("account") != account_id or signed.get("document") != _digest(asdict(document)):
        raise ImportConflict("Account or import content changed. Preview again.")
    fingerprint = _digest(signed)
    try:
        with transaction.atomic():
            account = PlatformAccount.objects.select_for_update().filter(pk=account_id, user=user, platform="devpost").first()
            if not account or account.handle != document.handle or account.handle != signed.get("handle") or account.updated_at.isoformat() != signed.get("account_updated_at"):
                raise ImportConflict("Linked Devpost account changed. Preview again.")
            prior = DevpostImportRun.objects.filter(user=user, request_fingerprint=fingerprint, status="completed").first()
            if prior:
                return prior
            public, state, event_by_external, project_by_external, submission_by_external = inspect_import(user, document, lock=True)
            if state != signed.get("state") or public["conflicts"]:
                raise ImportConflict()
            events = {submission.event.external_id: submission.event for project in document.projects for submission in project.submissions}
            event_actions = {item["event_url"]: item["event_action"]
                             for project in public["projects"] for item in project["submissions"]}
            participation_creates = {item["event_url"] for project in public["projects"]
                                     for item in project["submissions"] if item["participation_action"] == "create"}
            submitted_events = {submission.event.external_id for project in document.projects
                                for submission in project.submissions if submission.status == "submitted"}
            counts = {"events_created": 0, "participations_created": 0, "projects_created": 0, "submissions_created": 0,
                      "created": 0, "updated": 0, "skipped": 0}
            record_ids = {"events": [], "participations": [], "projects": [], "submissions": []}
            warnings = []
            for key, incoming in events.items():
                action = event_actions[incoming.event_url]
                current = event_by_external.get(key)
                if action == "create":
                    current = HackathonEvent.objects.create(owner=user, source="devpost", external_id=key, name=incoming.name,
                        event_url=incoming.event_url, organizer=incoming.organizer, start_date=incoming.start_date,
                        end_date=incoming.end_date, format=incoming.format)
                    counts["events_created"] += 1; counts["created"] += 1
                elif action == "update":
                    for field in ("name", "event_url", "organizer", "start_date", "end_date", "format"):
                        setattr(current, field, getattr(incoming, field))
                    current.save(); counts["updated"] += 1
                else:
                    counts["skipped"] += 1
                    if action == "protected": warnings.append(f"Protected event skipped: {incoming.event_url}")
                event_by_external[key] = current
                record_ids["events"].append(current.pk)
                if incoming.event_url in participation_creates:
                    participation = HackathonParticipation.objects.create(
                        user=user, event=current,
                        status=HackathonParticipation.Status.SUBMITTED if key in submitted_events else HackathonParticipation.Status.REGISTERED,
                    )
                    record_ids["participations"].append(participation.pk)
                    counts["participations_created"] += 1; counts["created"] += 1
                else:
                    counts["skipped"] += 1
            for incoming, planned in zip(document.projects, public["projects"]):
                action = planned["action"]
                current = project_by_external.get(incoming.external_id)
                if action == "create":
                    current = HackathonProject.objects.create(owner=user, source="devpost", external_id=incoming.external_id,
                        title=incoming.title, project_url=incoming.project_url, description=incoming.description, repository_url=incoming.repository_url,
                        demo_url=incoming.demo_url, technologies=list(incoming.technologies))
                    counts["projects_created"] += 1; counts["created"] += 1
                elif action == "update":
                    for field in ("title", "project_url", "description", "repository_url", "demo_url"):
                        setattr(current, field, getattr(incoming, field))
                    current.technologies = list(incoming.technologies)
                    current.save(); counts["updated"] += 1
                else:
                    counts["skipped"] += 1
                    if action == "protected": warnings.append(f"Protected project skipped: {incoming.project_url}")
                project_by_external[incoming.external_id] = current
                record_ids["projects"].append(current.pk)
                for submitted, planned_submission in zip(incoming.submissions, planned["submissions"]):
                    action = planned_submission["action"]
                    current_submission = submission_by_external.get(submitted.external_id)
                    if action == "create":
                        current_submission = HackathonSubmission.objects.create(owner=user, source="devpost", external_id=submitted.external_id,
                            event=event_by_external[submitted.event.external_id], project=current,
                            status=submitted.status, submission_url=submitted.submission_url)
                        counts["submissions_created"] += 1; counts["created"] += 1
                    elif action == "update":
                        current_submission.status = submitted.status
                        current_submission.submission_url = submitted.submission_url
                        current_submission.save(); counts["updated"] += 1
                    else:
                        counts["skipped"] += 1
                        if action == "protected": warnings.append(f"Protected submission skipped: {submitted.event.event_url}")
                    record_ids["submissions"].append(current_submission.pk)
            result = {**counts, "warnings": warnings, "record_ids": record_ids,
                      "potential_manual_duplicates": public["potential_manual_duplicates"]}
            return DevpostImportRun.objects.create(user=user, linked_account=account, profile_handle=account.handle,
                status="completed", request_fingerprint=fingerprint, projects_processed=len(document.projects),
                created_count=counts["created"], updated_count=counts["updated"], skipped_count=counts["skipped"],
                result=result, completed_at=timezone.now())
    except (IntegrityError, ModelValidationError) as exc:
        raise ImportConflict("Import conflicts with current records. Preview again.") from exc
