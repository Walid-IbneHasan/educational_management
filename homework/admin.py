from django.contrib import admin
from homework.models import Homework, HomeworkSubmission


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "institution",
        "curriculum_track",
        "section",
        "subject",
        "due_date",
        "created_by",
        "created_at",
        "is_active",
    )
    list_filter = ("institution", "section", "subject", "is_active")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("homework", "student", "submitted", "submission_date", "updated_by")
    list_filter = ("submitted",)
    search_fields = ("student__email", "homework__title")
    readonly_fields = ("updated_at",)
