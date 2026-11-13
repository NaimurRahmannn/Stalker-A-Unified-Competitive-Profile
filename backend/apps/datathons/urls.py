from django.urls import path

from .views import KaggleCapabilitiesView, KaggleManualTrackView, KaggleOverviewView, KaggleSyncStatusView, KaggleSyncView


urlpatterns = [
    path("kaggle/overview/", KaggleOverviewView.as_view(), name="kaggle-overview"),
    path("kaggle/manual/<str:track>/", KaggleManualTrackView.as_view(), name="kaggle-manual-track"),
    path("kaggle/capabilities/", KaggleCapabilitiesView.as_view(), name="kaggle-capabilities"),
    path("kaggle/sync/", KaggleSyncView.as_view(), name="kaggle-sync"),
    path("kaggle/sync-status/", KaggleSyncStatusView.as_view(), name="kaggle-sync-status"),
]
