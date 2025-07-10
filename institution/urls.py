from django.urls import path
from .views import (
    CurriculumTrackFeeViewSet,
    InstitutionFeeViewSet,
    InstitutionInfoViewSet,
    MyInstitutionView,
    GlobalCurriculumTrackViewSet,
    GlobalStreamViewSet,
    GlobalSubjectViewSet,
    GlobalModuleViewSet,
    GlobalUnitViewSet,
    GlobalLessonViewSet,
    GlobalMicroLessonViewSet,
    CurriculumTrackViewSet,
    SectionViewSet,
    StreamViewSet,
    StudentFeeViewSet,
    SubjectViewSet,
    ModuleViewSet,
    UnitViewSet,
    LessonViewSet,
    MicroLessonViewSet,
    TeacherEnrollmentViewSet,
    StudentEnrollmentViewSet,
    MyCurriculumTrackViewSet,
    MySectionViewSet,
    MySubjectViewSet,
    MySubjectByInstitutionViewSet,
)

urlpatterns = [
    path(
        "",
        InstitutionInfoViewSet.as_view({"get": "list", "post": "create"}),
        name="institution-info-list",
    ),
    path(
        "<uuid:pk>/",
        InstitutionInfoViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="institution-info-detail",
    ),
    path(
        "my-institution/",
        MyInstitutionView.as_view(),
        name="my-institution",
    ),
    path(
        "my-curriculum-tracks/",
        MyCurriculumTrackViewSet.as_view({"get": "list"}),
        name="my-curriculum-track-list",
    ),
    path(
        "my-sections/",
        MySectionViewSet.as_view({"get": "list"}),
        name="my-section-list",
    ),
    path(
        "my-subjects/",
        MySubjectViewSet.as_view({"get": "list"}),
        name="my-subject-list",
    ),
    path(
        "my-subjects/by-institution/",
        MySubjectByInstitutionViewSet.as_view({"get": "list"}),
        name="my-subject-by-institution-list",
    ),
    path(
        "global-curriculum-tracks/",
        GlobalCurriculumTrackViewSet.as_view({"get": "list", "post": "create"}),
        name="global-curriculum-track-list",
    ),
    path(
        "global-curriculum-tracks/<uuid:pk>/",
        GlobalCurriculumTrackViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-curriculum-track-detail",
    ),
    path(
        "global-streams/",
        GlobalStreamViewSet.as_view({"get": "list", "post": "create"}),
        name="global-stream-list",
    ),
    path(
        "global-streams/<uuid:pk>/",
        GlobalStreamViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-stream-detail",
    ),
    path(
        "global-subjects/",
        GlobalSubjectViewSet.as_view({"get": "list", "post": "create"}),
        name="global-subject-list",
    ),
    path(
        "global-subjects/<uuid:pk>/",
        GlobalSubjectViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-subject-detail",
    ),
    path(
        "global-modules/",
        GlobalModuleViewSet.as_view({"get": "list", "post": "create"}),
        name="global-module-list",
    ),
    path(
        "global-modules/<uuid:pk>/",
        GlobalModuleViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-module-detail",
    ),
    path(
        "global-units/",
        GlobalUnitViewSet.as_view({"get": "list", "post": "create"}),
        name="global-unit-list",
    ),
    path(
        "global-units/<uuid:pk>/",
        GlobalUnitViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-unit-detail",
    ),
    path(
        "global-lessons/",
        GlobalLessonViewSet.as_view({"get": "list", "post": "create"}),
        name="global-lesson-list",
    ),
    path(
        "global-lessons/<uuid:pk>/",
        GlobalLessonViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-lesson-detail",
    ),
    path(
        "global-micro-lessons/",
        GlobalMicroLessonViewSet.as_view({"get": "list", "post": "create"}),
        name="global-micro-lesson-list",
    ),
    path(
        "global-micro-lessons/<uuid:pk>/",
        GlobalMicroLessonViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="global-micro-lesson-detail",
    ),
    path(
        "curriculum-tracks/",
        CurriculumTrackViewSet.as_view({"get": "list", "post": "create"}),
        name="curriculum-track-list",
    ),
    path(
        "curriculum-tracks/<uuid:pk>/",
        CurriculumTrackViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="curriculum-track-detail",
    ),
    path(
        "sections/",
        SectionViewSet.as_view({"get": "list", "post": "create"}),
        name="section-list",
    ),
    path(
        "sections/<uuid:pk>/",
        SectionViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="section-detail",
    ),
    path(
        "streams/",
        StreamViewSet.as_view({"get": "list", "post": "create"}),
        name="stream-list",
    ),
    path(
        "streams/<uuid:pk>/",
        StreamViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="stream-detail",
    ),
    path(
        "subjects/",
        SubjectViewSet.as_view({"get": "list", "post": "create"}),
        name="subject-list",
    ),
    path(
        "subjects/<uuid:pk>/",
        SubjectViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="subject-detail",
    ),
    path(
        "modules/",
        ModuleViewSet.as_view({"get": "list", "post": "create"}),
        name="module-list",
    ),
    path(
        "modules/<uuid:pk>/",
        ModuleViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="module-detail",
    ),
    path(
        "units/",
        UnitViewSet.as_view({"get": "list", "post": "create"}),
        name="unit-list",
    ),
    path(
        "units/<uuid:pk>/",
        UnitViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="unit-detail",
    ),
    path(
        "lessons/",
        LessonViewSet.as_view({"get": "list", "post": "create"}),
        name="lesson-list",
    ),
    path(
        "lessons/<uuid:pk>/",
        LessonViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="lesson-detail",
    ),
    path(
        "micro-lessons/",
        MicroLessonViewSet.as_view({"get": "list", "post": "create"}),
        name="micro-lesson-list",
    ),
    path(
        "micro-lessons/<uuid:pk>/",
        MicroLessonViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="micro-lesson-detail",
    ),
    path(
        "teacher-enrollments/",
        TeacherEnrollmentViewSet.as_view({"get": "list", "post": "create"}),
        name="teacher-enrollment-list",
    ),
    path(
        "teacher-enrollments/<uuid:pk>/",
        TeacherEnrollmentViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="teacher-enrollment-detail",
    ),
    path(
        "student-enrollments/",
        StudentEnrollmentViewSet.as_view({"get": "list", "post": "create"}),
        name="student-enrollment-list",
    ),
    path(
        "student-enrollments/<uuid:pk>/",
        StudentEnrollmentViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="student-enrollment-detail",
    ),
    path(
        "student-enrollments/by-section/",
        StudentEnrollmentViewSet.as_view({"get": "by_section"}),
        name="student-enrollment-by-section",
    ),
    path(
        "fees/institution/",
        InstitutionFeeViewSet.as_view({"get": "list", "post": "create"}),
        name="institution-fee-list",
    ),
    path(
        "fees/institution/<uuid:pk>/",
        InstitutionFeeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="institution-fee-detail",
    ),
    path(
        "fees/curriculum-tracks/",
        CurriculumTrackFeeViewSet.as_view({"get": "list", "post": "create"}),
        name="curriculum-track-fee-list",
    ),
    path(
        "fees/curriculum-tracks/<uuid:pk>/",
        CurriculumTrackFeeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="curriculum-track-fee-detail",
    ),
    path(
        "fees/students/",
        StudentFeeViewSet.as_view({"get": "list", "post": "create"}),
        name="student-fee-list",
    ),
    path(
        "fees/students/<uuid:pk>/",
        StudentFeeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="student-fee-detail",
    ),
]
