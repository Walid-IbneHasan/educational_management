from django.urls import path
from syllabus.views import SyllabusViewSet

app_name = "syllabus"

urlpatterns = [
    path(
        "",
        SyllabusViewSet.as_view({"get": "list", "post": "create"}),
        name="syllabus-list",
    ),
    path(
        "<uuid:pk>/",
        SyllabusViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="syllabus-detail",
    ),
]
