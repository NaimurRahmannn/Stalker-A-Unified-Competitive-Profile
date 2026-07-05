from django.urls import path

from apps.profiles.views import PublicProfileView


urlpatterns = [
    path("<str:username>/", PublicProfileView.as_view(), name="public-profile"),
]

