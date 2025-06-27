from django.urls import path, include
from rest_framework.routers import DefaultRouter
from homework.views import HomeworkViewSet, HomeworkSubmissionViewSet

app_name = "homework"

router = DefaultRouter()
router.register(r"homeworks", HomeworkViewSet, basename="homework")
router.register(r"submissions", HomeworkSubmissionViewSet, basename="submission")

urlpatterns = [
    path("", include(router.urls)),
]
