from rest_framework.routers import DefaultRouter

from apps.connectors.views import PlatformAccountViewSet


router = DefaultRouter()
router.register("platform-accounts", PlatformAccountViewSet, basename="platform-account")

urlpatterns = router.urls
