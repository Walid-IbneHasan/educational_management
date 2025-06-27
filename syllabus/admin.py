from django.contrib import admin
from .models import Syllabus


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "institution",
        "curriculum_track",
        "section",
        "subject",
        "purpose",
        "created_by",
        "created_at",
        "is_active",
    )
    list_filter = ("institution", "purpose", "is_active")
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("modules", "units", "lessons", "micro_lessons")
