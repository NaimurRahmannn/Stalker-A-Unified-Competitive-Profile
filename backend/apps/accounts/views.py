from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ExternalAccount
from apps.accounts.selectors import get_user_external_accounts
from apps.accounts.serializers import (
    ConnectExternalAccountSerializer,
    ExternalAccountSerializer,
    ProfileSnapshotSummarySerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from apps.accounts.services import connect_external_account, sync_external_account


def _tokens_for_user(user) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "tokens": _tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer
    http_method_names = ["patch", "options", "head"]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


class RegisterAPIView(RegisterView):
    pass


class MeAPIView(MeView):
    pass


class ExternalAccountListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExternalAccountSerializer

    def get_queryset(self):
        return get_user_external_accounts(self.request.user)


class ExternalAccountConnectAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ConnectExternalAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        external_account, snapshot = connect_external_account(
            user=request.user,
            source=serializer.validated_data["source"],
            handle_or_slug=serializer.validated_data["handle_or_slug"],
        )
        return Response(
            {
                "account": ExternalAccountSerializer(external_account).data,
                "latest_snapshot": ProfileSnapshotSummarySerializer(snapshot).data,
            },
            status=status.HTTP_200_OK,
        )


class ExternalAccountSyncAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        external_account = get_object_or_404(ExternalAccount, pk=pk, user=request.user)
        snapshot = sync_external_account(external_account)
        return Response(ProfileSnapshotSummarySerializer(snapshot).data, status=status.HTTP_200_OK)
