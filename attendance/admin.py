from django.contrib import admin
from attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "institution",
        "section",
        "subject",
        "date",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("institution", "date", "status", "section", "subject")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "institution__name",
        "subject__name__name",
    )
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Limit to institutions where user is a member
            from user_management.models.authentication import InstitutionMembership

            institutions = InstitutionMembership.objects.filter(
                user=request.user
            ).values_list("institution_id", flat=True)
            qs = qs.filter(institution__in=institutions)
        return qs
