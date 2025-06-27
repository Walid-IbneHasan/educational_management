from django.contrib import admin
from notice.models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "institution",
        "created_by",
        "created_at",
        "is_active",
        "notice_type",
        "target_audience",
    )
    list_filter = ("institution", "is_active")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
