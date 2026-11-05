"""Owner-only, non-destructive review of possible manual/Devpost matches."""

from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.hackathons.models import HackathonDuplicateReview, HackathonEvent, HackathonProject


def canonical_url(value):
    if not value:
        return ""
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return ""
        # Hostnames and a trailing slash are safe to normalize. Paths and
        # query strings can identify different resources, so preserve them.
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.hostname.lower()}{port}{parts.path.rstrip('/')}{'?' + parts.query if parts.query else ''}"
    except ValueError:
        return ""


def match_reason(record_type, manual, imported):
    if record_type == "event":
        return "Matching event URL" if canonical_url(manual.event_url) and canonical_url(manual.event_url) == canonical_url(imported.event_url) else ""
    for field in ("project_url", "repository_url", "demo_url"):
        left = canonical_url(getattr(manual, field))
        if left and left in {canonical_url(imported.project_url), canonical_url(imported.repository_url), canonical_url(imported.demo_url)}:
            return f"Matching {field.replace('_', ' ')}"
    return ""


def record_summary(record):
    if isinstance(record, HackathonProject):
        return {"id": record.pk, "title": record.title, "project_url": record.project_url,
                "repository_url": record.repository_url, "demo_url": record.demo_url,
                "source": record.source, "is_public": record.is_public}
    return {"id": record.pk, "name": record.name, "event_url": record.event_url, "source": record.source}


def review_summary(review):
    project = review.record_type == "project"
    manual = review.manual_project if project else review.manual_event
    imported = review.imported_project if project else review.imported_event
    return {"id": review.pk, "record_type": review.record_type, "manual": record_summary(manual),
            "imported": record_summary(imported), "decision": review.decision,
            "reason": match_reason(review.record_type, manual, imported) or "Previously reviewed pair",
            "created_at": review.created_at, "updated_at": review.updated_at}


def candidate_pairs(user):
    """Return at most 50 deterministic URL suggestions, never inferred merges."""
    candidates = []
    for record_type, model, url_fields in (
        ("project", HackathonProject, ("project_url", "repository_url", "demo_url")),
        ("event", HackathonEvent, ("event_url",)),
    ):
        imported_rows = list(model.objects.filter(owner=user, source="devpost").order_by("-updated_at", "-pk")[:50])
        urls = {getattr(row, field) for row in imported_rows for field in url_fields if getattr(row, field)}
        if not urls:
            continue
        lookup = Q()
        for field in url_fields:
            lookup |= Q(**{f"{field}__in": urls})
        manual_rows = list(model.objects.filter(owner=user, source="manual").filter(lookup).order_by("-updated_at", "-pk")[:250])
        # Exact DB matches are cheap; also consider recent records whose URL
        # differs only in safe normalization (scheme, host case, trailing slash).
        if len(manual_rows) < 250:
            seen = {row.pk for row in manual_rows}
            for row in model.objects.filter(owner=user, source="manual").order_by("-updated_at", "-pk")[:250]:
                if row.pk not in seen:
                    manual_rows.append(row)
                    seen.add(row.pk)
                if len(manual_rows) == 250:
                    break
        for imported in imported_rows:
            for manual in manual_rows:
                reason = match_reason(record_type, manual, imported)
                if reason:
                    candidates.append((record_type, manual, imported, reason))
                    if len(candidates) == 50:
                        return candidates
    return candidates


class ReviewPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


def validated_decision(data, *, creating):
    expected = {"record_type", "manual_id", "imported_id", "decision"} if creating else {"decision"}
    if not isinstance(data, dict) or set(data) != expected:
        raise ValidationError({"detail": "Provide only the required review fields."})
    decision = data.get("decision")
    if decision not in HackathonDuplicateReview.Decision.values:
        raise ValidationError({"decision": "Choose unresolved, related, or distinct."})
    if creating:
        if data.get("record_type") not in HackathonDuplicateReview.RecordType.values:
            raise ValidationError({"record_type": "Choose project or event."})
        if any(type(data[key]) is not int or data[key] < 1 for key in ("manual_id", "imported_id")):
            raise ValidationError({"detail": "Record IDs must be positive integers."})
        if data["manual_id"] == data["imported_id"]:
            raise ValidationError({"detail": "A record cannot be linked to itself."})
    return decision


class DuplicateReviewListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = HackathonDuplicateReview.objects.filter(owner=request.user).select_related(
            "manual_project", "imported_project", "manual_event", "imported_event"
        ).order_by("-updated_at", "-pk")
        paginator = ReviewPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        reviews = paginator.get_paginated_response([review_summary(row) for row in page]).data
        pairs = candidate_pairs(request.user)
        project_manual_ids = [manual.pk for kind, manual, _, _ in pairs if kind == "project"]
        project_imported_ids = [imported.pk for kind, _, imported, _ in pairs if kind == "project"]
        event_manual_ids = [manual.pk for kind, manual, _, _ in pairs if kind == "event"]
        event_imported_ids = [imported.pk for kind, _, imported, _ in pairs if kind == "event"]
        saved = list(HackathonDuplicateReview.objects.filter(owner=request.user).filter(
            Q(record_type="project", manual_project_id__in=project_manual_ids, imported_project_id__in=project_imported_ids) |
            Q(record_type="event", manual_event_id__in=event_manual_ids, imported_event_id__in=event_imported_ids)
        ))
        decisions = {(row.record_type, row.manual_project_id or row.manual_event_id,
                      row.imported_project_id or row.imported_event_id): row for row in saved}
        candidates = []
        for kind, manual, imported, reason in pairs:
            review = decisions.get((kind, manual.pk, imported.pk))
            candidates.append({"id": review.pk if review else None, "record_type": kind,
                               "manual": record_summary(manual), "imported": record_summary(imported),
                               "reason": reason, "decision": review.decision if review else "unresolved"})
        return Response({"candidates": candidates, "reviews": reviews})

    def post(self, request):
        decision = validated_decision(request.data, creating=True)
        kind = request.data["record_type"]
        model = HackathonProject if kind == "project" else HackathonEvent
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            manual = get_object_or_404(model.objects.select_for_update(), pk=request.data["manual_id"], owner=request.user, source="manual")
            imported = get_object_or_404(model.objects.select_for_update(), pk=request.data["imported_id"], owner=request.user, source="devpost")
            if not match_reason(kind, manual, imported):
                raise ValidationError({"detail": "These records have no matching URL signal."})
            fields = ({"manual_project": manual, "imported_project": imported} if kind == "project" else
                      {"manual_event": manual, "imported_event": imported})
            try:
                lookup = {"owner": request.user, "record_type": kind, **fields}
                review = HackathonDuplicateReview.objects.select_for_update(of=("self",)).filter(**lookup).first()
                created = review is None
                if created:
                    review = HackathonDuplicateReview.objects.create(**lookup, decision=decision)
                elif review.decision != decision:
                    review.decision = decision
                    review.save(update_fields=("decision", "updated_at"))
            except IntegrityError as exc:
                raise ValidationError({"detail": "Review changed concurrently. Retry."}) from exc
        return Response(review_summary(review), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DuplicateReviewDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        decision = validated_decision(request.data, creating=False)
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            review = get_object_or_404(HackathonDuplicateReview.objects.select_for_update(of=("self",)).select_related(
                "manual_project", "imported_project", "manual_event", "imported_event"
            ), pk=pk, owner=request.user)
            if review.decision != decision:
                review.decision = decision
                review.save(update_fields=("decision", "updated_at"))
        return Response(review_summary(review))
