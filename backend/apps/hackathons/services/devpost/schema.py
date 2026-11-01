"""Strict STALKER JSON v1 normalization, independent of acquisition method."""

from dataclasses import dataclass
from datetime import date
import json

from rest_framework.exceptions import APIException, ValidationError

from .identity import event_reference, external_id, external_url, profile_reference, project_reference


MAX_BYTES = 1_048_576
MAX_PROJECTS = 100
MAX_SUBMISSIONS = 20


class PayloadTooLarge(APIException):
    status_code = 413
    default_detail = "Import exceeds 1 MB."


@dataclass(frozen=True)
class NormalizedEvent:
    external_id: str
    name: str
    event_url: str
    organizer: str = ""
    start_date: date | None = None
    end_date: date | None = None
    format: str = "unknown"


@dataclass(frozen=True)
class NormalizedSubmission:
    external_id: str
    event: NormalizedEvent
    status: str
    submission_url: str = ""


@dataclass(frozen=True)
class NormalizedProject:
    external_id: str
    project_url: str
    title: str
    description: str
    repository_url: str
    demo_url: str
    technologies: tuple[str, ...]
    submissions: tuple[NormalizedSubmission, ...]


@dataclass(frozen=True)
class NormalizedDocument:
    handle: str
    projects: tuple[NormalizedProject, ...]


def _object(value, allowed, label):
    if not isinstance(value, dict):
        raise ValidationError({label: "Expected an object."})
    unknown = set(value) - set(allowed)
    if unknown:
        raise ValidationError({label: f"Unsupported field: {sorted(unknown)[0]}."})
    return value


def _string(value, label, limit, required=False):
    if not isinstance(value, str):
        raise ValidationError({label: "Expected text."})
    value = value.strip()
    if len(value) > limit or (required and not value):
        raise ValidationError({label: f"Enter {'nonempty ' if required else ''}text of at most {limit} characters."})
    return value


def _date(value, label):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 10:
        raise ValidationError({label: "Use YYYY-MM-DD."})
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError({label: "Use a valid YYYY-MM-DD date."}) from exc


def normalize(document, linked_handle: str) -> NormalizedDocument:
    try:
        if len(json.dumps(document, ensure_ascii=False).encode("utf-8")) > MAX_BYTES:
            raise PayloadTooLarge()
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValidationError({"detail": "Invalid JSON structure."}) from exc
    _object(document, {"format_version", "profile_url", "projects"}, "document")
    if type(document.get("format_version")) is not int or document["format_version"] != 1:
        raise ValidationError({"format_version": "Only STALKER format version 1 is supported."})
    if not isinstance(document.get("profile_url"), str) or "://" not in document["profile_url"]:
        raise ValidationError({"profile_url": "Enter the linked Devpost profile URL."})
    handle, _ = profile_reference(document["profile_url"])
    if handle != linked_handle:
        raise ValidationError({"profile_url": "Profile must match the linked Devpost account."})
    raw_projects = document.get("projects")
    if not isinstance(raw_projects, list) or len(raw_projects) > MAX_PROJECTS:
        raise ValidationError({"projects": "Provide a list of at most 100 projects."})
    projects = []
    seen_projects = set()
    seen_events = {}
    for raw in raw_projects:
        _object(raw, {"project_url", "title", "description", "repository_url", "demo_url", "technologies", "submissions"}, "project")
        project_url = project_reference(raw.get("project_url", ""))
        if project_url in seen_projects:
            raise ValidationError({"projects": "Duplicate Devpost project URL."})
        seen_projects.add(project_url)
        title = _string(raw.get("title", ""), "title", 500, required=True)
        description = _string(raw.get("description", ""), "description", 5000)
        repository_url = _string(raw.get("repository_url", ""), "repository_url", 500)
        demo_url = _string(raw.get("demo_url", ""), "demo_url", 500)
        for url in (repository_url, demo_url):
            if url:
                external_url(url)
        technologies = raw.get("technologies", [])
        if not isinstance(technologies, list) or len(technologies) > 30:
            raise ValidationError({"technologies": "Provide at most 30 technologies."})
        technologies = tuple(_string(item, "technology", 100, required=True) for item in technologies)
        raw_submissions = raw.get("submissions", [])
        if not isinstance(raw_submissions, list) or len(raw_submissions) > MAX_SUBMISSIONS:
            raise ValidationError({"submissions": "Provide at most 20 submissions per project."})
        submissions = []
        seen_for_project = set()
        for item in raw_submissions:
            _object(item, {"hackathon_name", "hackathon_url", "organizer", "start_date", "end_date", "format", "status", "submission_url"}, "submission")
            event_url = event_reference(item.get("hackathon_url", ""))
            name = _string(item.get("hackathon_name", ""), "hackathon_name", 500, required=True)
            organizer = _string(item.get("organizer", ""), "organizer", 255)
            start = _date(item.get("start_date"), "start_date")
            end = _date(item.get("end_date"), "end_date")
            if start and end and end < start:
                raise ValidationError({"end_date": "End date cannot precede start date."})
            event_format = item.get("format", "unknown")
            if not isinstance(event_format, str) or event_format not in {"online", "in_person", "hybrid", "unknown"}:
                raise ValidationError({"format": "Unsupported event format."})
            event = NormalizedEvent(external_id("event", handle, event_url), name, event_url, organizer, start, end, event_format)
            if event_url in seen_events and seen_events[event_url] != event:
                raise ValidationError({"hackathon_url": "Conflicting details for the same hackathon."})
            seen_events[event_url] = event
            if event_url in seen_for_project:
                raise ValidationError({"submissions": "Duplicate project and hackathon relationship."})
            seen_for_project.add(event_url)
            status = item.get("status")
            if not isinstance(status, str) or status not in {"draft", "submitted", "withdrawn"}:
                raise ValidationError({"status": "Provide draft, submitted, or withdrawn."})
            submission_url = _string(item.get("submission_url", ""), "submission_url", 500)
            if submission_url:
                external_url(submission_url)
            submissions.append(NormalizedSubmission(external_id("submission", handle, project_url, event_url), event, status, submission_url))
        projects.append(NormalizedProject(external_id("project", handle, project_url), project_url, title, description, repository_url, demo_url, technologies, tuple(submissions)))
    return NormalizedDocument(handle, tuple(projects))
