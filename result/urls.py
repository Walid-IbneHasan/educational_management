from django.urls import path
from . import views

urlpatterns = [
    path(
        "student/<uuid:student_id>/",
        views.StudentResultView.as_view(),
        name="student-result",
    ),
    path("section/", views.SectionResultView.as_view(), name="section-result"),
]
