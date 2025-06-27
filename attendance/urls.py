from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet

app_name = "attendance"

router = DefaultRouter()
router.register("", AttendanceViewSet, basename="attendance")

urlpatterns = router.urls
