from rest_framework import serializers

from user_management.models.authentication import InstitutionMembership
from payment_management.serializers.bkash import PaymentCreateSerializer
from institution.models import StudentEnrollment, InstitutionInfo
from institution.serializers import StudentEnrollmentSerializer
from payment_management.models.fees import StudentFeePayment, InstitutionPaymentTracker
from datetime import datetime


class StudentFeePaymentSerializer(serializers.ModelSerializer):
    student_enrollment = StudentEnrollmentSerializer(read_only=True)
    student_enrollment_id = serializers.UUIDField(write_only=True)
    month = serializers.DateField(
        format="%Y-%m", input_formats=["%Y-%m", "%Y-%m-%d"]
    )  # Allow both formats
    bkash_payment_id = serializers.CharField(
        read_only=True, source="bkash_payment.payment_id"
    )

    class Meta:
        model = StudentFeePayment
        fields = [
            "id",
            "student_enrollment",
            "student_enrollment_id",
            "bkash_payment_id",
            "amount",
            "month",
            "status",
            "scholarship_applied",
            "scholarship_amount",
        ]
        read_only_fields = [
            "amount",
            "status",
            "scholarship_applied",
            "scholarship_amount",
        ]

    def validate(self, data):
        student_enrollment = StudentEnrollment.objects.filter(
            id=data.get("student_enrollment_id")
        ).first()
        if not student_enrollment:
            raise serializers.ValidationError(
                {"student_enrollment_id": "Invalid student enrollment."}
            )

        # Check if user is parent or student
        user = self.context["request"].user
        if not (
            user == student_enrollment.user
            or InstitutionMembership.objects.filter(
                user=user, institution=student_enrollment.institution, role="parent"
            ).exists()
        ):
            raise serializers.ValidationError(
                {"student_enrollment_id": "Not authorized to pay for this student."}
            )

        # Normalize month to first of the month
        month = data["month"]
        data["month"] = month.replace(day=1)

        # Check for duplicate payment for the same month
        if StudentFeePayment.objects.filter(
            student_enrollment=student_enrollment,
            month=data["month"],
            status__in=["pending", "completed"],
        ).exists():
            raise serializers.ValidationError(
                {"month": "Payment for this month already exists."}
            )

        return data


class InstitutionPaymentTrackerSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    student_name = serializers.CharField(
        source="student_fee_payment.student_enrollment.user.get_full_name",
        read_only=True,
    )

    class Meta:
        model = InstitutionPaymentTracker
        fields = [
            "id",
            "institution",
            "institution_name",
            "student_name",
            "amount",
            "is_disbursed",
            "disbursed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["institution", "amount", "created_at", "updated_at"]
