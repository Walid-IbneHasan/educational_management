from django.urls import path
from .views import ScholarshipViewSet

urlpatterns = [
    path(
        "scholarships/",
        ScholarshipViewSet.as_view({"get": "list", "post": "create"}),
        name="scholarship-list",
    ),
    path(
        "scholarships/<uuid:pk>/",
        ScholarshipViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="scholarship-detail",
    ),
]
