from django.urls import path

from apps.profiles.views import PublicHackathonPortfolioView, PublicProfileView


urlpatterns = [
    path("<str:username>/hackathons/", PublicHackathonPortfolioView.as_view(), name="public-hackathons"),
    path("<str:username>/", PublicProfileView.as_view(), name="public-profile"),
]

