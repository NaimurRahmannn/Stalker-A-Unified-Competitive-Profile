from django.urls import path

from .views import KaggleOverviewView


urlpatterns = [path("kaggle/overview/", KaggleOverviewView.as_view(), name="kaggle-overview")]
