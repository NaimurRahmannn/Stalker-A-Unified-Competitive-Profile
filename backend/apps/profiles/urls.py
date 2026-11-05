from django.urls import path

from apps.profiles.views import PublicHackathonPortfolioView, PublicHackathonProjectDetailView, PublicProfileView


urlpatterns = [
    path("<str:username>/hackathons/projects/<int:project_id>/", PublicHackathonProjectDetailView.as_view(), name="public-hackathon-project-detail"),
    path("<str:username>/hackathons/", PublicHackathonPortfolioView.as_view(), name="public-hackathons"),
    path("<str:username>/", PublicProfileView.as_view(), name="public-profile"),
]

