from django.urls import path

from .views import KaggleOverviewView, KaggleSyncStatusView, KaggleSyncView


urlpatterns = [
    path("kaggle/overview/", KaggleOverviewView.as_view(), name="kaggle-overview"),
    path("kaggle/sync/", KaggleSyncView.as_view(), name="kaggle-sync"),
    path("kaggle/sync-status/", KaggleSyncStatusView.as_view(), name="kaggle-sync-status"),
]
