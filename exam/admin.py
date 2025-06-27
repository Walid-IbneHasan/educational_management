from django.contrib import admin
from .models import Exam, ExamMark


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject",
        "exam_type",
        "exam_date",
        "total_marks",
        "is_active",
    ]
    list_filter = ["exam_type", "is_active", "curriculum_track"]
    search_fields = ["title", "subject__name__name"]


@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ["student", "exam", "marks_obtained"]
    list_filter = ["exam__exam_type", "exam__curriculum_track"]
    search_fields = ["student__email", "student__first_name", "exam__title"]
