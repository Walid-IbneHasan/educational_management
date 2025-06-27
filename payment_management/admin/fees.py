from django.contrib import admin
from payment_management.models.fees import InstitutionPaymentTracker, StudentFeePayment
from payment_management.models.bkash import BkashPayment


@admin.register(StudentFeePayment)
class StudentFeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "institution_display",
        "student_name",
        "amount",
        "month",
        "scholarship_applied",
    )
    list_filter = ["month"]
    search_fields = (
        "student_enrollment__institution__name",
        "student_enrollment__user__first_name",
        "student_enrollment__user__last_name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "month"

    def institution_display(self, obj):
        return obj.student_enrollment.institution.name

    institution_display.short_description = "Institution"

    def student_name(self, obj):
        user = obj.student_enrollment.user
        return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or str(
            user
        )

    student_name.short_description = "Student"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "student_enrollment__institution",
                "student_enrollment__user",
                "bkash_payment",
            )
        )


@admin.register(InstitutionPaymentTracker)
class InstitutionPaymentTrackerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "institution",
        "student_fee_payment",
        "amount",
        "is_disbursed",
        "disbursed_at",
        "created_at",
    )
    list_filter = ("is_disbursed", "institution")
    search_fields = (
        "institution__name",
        "student_fee_payment__id",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BkashPayment)
class BkashPaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "order_id", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("payment_id", "order_id", "transaction_id")
    readonly_fields = (
        "id",
        "payment_id",
        "transaction_id",
        "order_id",
        "created_at",
        "updated_at",
    )
