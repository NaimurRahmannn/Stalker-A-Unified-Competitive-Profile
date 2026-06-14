from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import MeView, ProfileUpdateView, RegisterView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", TokenObtainPairView.as_view(), name="accounts-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="accounts-token-refresh"),
    path("me/", MeView.as_view(), name="accounts-me"),
    path("me/update/", ProfileUpdateView.as_view(), name="accounts-me-update"),
]
