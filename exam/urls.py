from django.urls import path
from . import views

urlpatterns = [
    path("", views.ExamListCreateView.as_view(), name="exam-list-create"),
    path("<uuid:pk>/", views.ExamDetailView.as_view(), name="exam-detail"),
    path(
        "created-exams/",
        views.TeacherCreatedExamsView.as_view(),
        name="teacher-created-exams",
    ),
    path(
        "marks/", views.ExamMarkListCreateView.as_view(), name="exam-mark-list-create"
    ),
    path(
        "marks/<uuid:pk>/", views.ExamMarkDetailView.as_view(), name="exam-mark-detail"
    ),
]
