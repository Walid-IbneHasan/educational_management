from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import SyllabusViewSet

app_name = "syllabus"

router = DefaultRouter()
router.register(r"syllabus", SyllabusViewSet, basename="syllabus")

urlpatterns = [
    path("", include(router.urls)),
]
