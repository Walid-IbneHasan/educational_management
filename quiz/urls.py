from django.urls import path
from . import views

urlpatterns = [
    path(
        "questions/",
        views.QuizQuestionListCreateView.as_view(),
        name="quiz-question-list-create",
    ),
    path(
        "questions/<uuid:pk>/",
        views.QuizQuestionDetailView.as_view(),
        name="quiz-question-detail",
    ),
    path("", views.QuizListCreateView.as_view(), name="quiz-list-create"),
    path("<uuid:pk>/", views.QuizDetailView.as_view(), name="quiz-detail"),
    path(
        "<uuid:pk>/questions/", views.QuizQuestionsView.as_view(), name="quiz-questions"
    ),
    path("<uuid:pk>/start/", views.QuizStartView.as_view(), name="quiz-start"),
    path("<uuid:pk>/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
    path("<uuid:pk>/grade/", views.QuizGradeView.as_view(), name="quiz-grade"),
    path("attempts/", views.QuizAttemptListView.as_view(), name="quiz-attempt-list"),
    path(
        "attempts/<uuid:pk>/",
        views.QuizAttemptDetailView.as_view(),
        name="quiz-attempt-detail",
    ),
    path(
        "parent-attempts/",
        views.ParentQuizAttemptListView.as_view(),
        name="parent-attempt-list",
    ),
]
