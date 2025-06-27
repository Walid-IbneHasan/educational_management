from django.urls import path
from user_management.views.admission_seeker import AdmissionRequestViewSet

app_name = "admission_seeker"

urlpatterns = [
    path(
        "admissions/",
        AdmissionRequestViewSet.as_view({"post": "create", "get": "list"}),
        name="admission-list",
    ),
    path(
        "admissions/<uuid:pk>/approve/",
        AdmissionRequestViewSet.as_view({"post": "approve"}),
        name="admission-approve",
    ),
    path(
        "admissions/<uuid:pk>/reject/",
        AdmissionRequestViewSet.as_view({"post": "reject"}),
        name="admission-reject",
    ),
    path(
        "institution-requests/",
        AdmissionRequestViewSet.as_view({"get": "institution_requests"}),
        name="institution-requests",
    ),
    path(
        "institution-approvals/",
        AdmissionRequestViewSet.as_view({"get": "institution_approvals"}),
        name="institution-approvals",
    ),
]
