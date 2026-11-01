"""Authenticated API for previewing and applying user-supplied Devpost data."""

from uuid import uuid4

from django.utils import timezone
from rest_framework import permissions, serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.connectors.models import PlatformAccount
from apps.hackathons.models import DevpostImportRun
from apps.hackathons.services.devpost.import_service import ImportConflict, apply_import, preview
from apps.hackathons.services.devpost.providers.user_json import UserJsonProvider
from apps.hackathons.services.devpost.schema import MAX_REQUEST_BYTES, RequestTooLarge, normalize


class ImportRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevpostImportRun
        fields = ("id", "profile_handle", "input_method", "status", "projects_processed", "created_count",
                  "updated_count", "skipped_count", "error_count", "result", "started_at", "completed_at")
        read_only_fields = fields


class ImportHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class DevpostImportBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        length = request._request.META.get("CONTENT_LENGTH", "")
        if length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            raise RequestTooLarge()
        if len(request._request.body) > MAX_REQUEST_BYTES:
            raise RequestTooLarge()

    def account(self, request):
        account = PlatformAccount.objects.filter(user=request.user, platform=PlatformAccount.Platform.DEVPOST).first()
        if account is None:
            raise NotFound("Link a Devpost profile before importing.")
        return account

    def document(self, request, supplied):
        account = self.account(request)
        data = UserJsonProvider().acquire(supplied)
        return account, normalize(data, account.handle)


class DevpostImportPreviewView(DevpostImportBase):
    def post(self, request):
        account, document = self.document(request, request.data)
        return Response(preview(request.user, account, document))


class DevpostImportListView(DevpostImportBase):
    def get(self, request):
        queryset = DevpostImportRun.objects.filter(user=request.user).order_by("-started_at", "-pk")
        paginator = ImportHistoryPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(ImportRunSerializer(page, many=True).data)

    def post(self, request):
        if not isinstance(request.data, dict) or not isinstance(request.data.get("preview_token"), str):
            raise ValidationError({"preview_token": "Preview the document before applying."})
        if len(request.data["preview_token"]) > 8192:
            raise ValidationError({"preview_token": "Preview token is too large."})
        account, document = self.document(request, request.data.get("document"))
        try:
            run = apply_import(request.user, account.pk, document, request.data["preview_token"])
        except ImportConflict as exc:
            DevpostImportRun.objects.create(
                user=request.user, linked_account=None, profile_handle=account.handle,
                status=DevpostImportRun.Status.FAILED, request_fingerprint=uuid4().hex,
                projects_processed=len(document.projects), error_count=1,
                result={"error": str(exc.detail)}, completed_at=timezone.now(),
            )
            raise
        return Response(ImportRunSerializer(run).data)


class DevpostImportDetailView(DevpostImportBase):
    def get(self, request, pk):
        run = DevpostImportRun.objects.filter(user=request.user, pk=pk).first()
        if run is None:
            raise NotFound("Import run not found.")
        return Response(ImportRunSerializer(run).data)
