from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    ExternalAccountConnectAPIView,
    ExternalAccountListAPIView,
    ExternalAccountSyncAPIView,
    MeAPIView,
    MeView,
    ProfileUpdateView,
    RegisterAPIView,
    RegisterView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", TokenObtainPairView.as_view(), name="accounts-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
    path("me/", MeView.as_view(), name="accounts-me"),
    path("me/update/", ProfileUpdateView.as_view(), name="accounts-me-update"),
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("accounts/", ExternalAccountListAPIView.as_view(), name="accounts-list"),
    path("accounts/connect/", ExternalAccountConnectAPIView.as_view(), name="accounts-connect"),
    path("accounts/<int:pk>/sync/", ExternalAccountSyncAPIView.as_view(), name="accounts-sync"),
]
