from django.db import models
from uuid import uuid4
from institution.models import InstitutionInfo, StudentEnrollment
from .bkash import BkashPayment


class StudentFeePayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    student_enrollment = models.ForeignKey(
        StudentEnrollment, on_delete=models.CASCADE, related_name="fee_payments"
    )
    bkash_payment = models.ForeignKey(
        BkashPayment, on_delete=models.CASCADE, related_name="fee_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  # Represents the month for which payment is made
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default="pending")
    scholarship_applied = models.BooleanField(default=False)
    scholarship_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

    def __str__(self):
        return f"{self.student_enrollment.user} - {self.month.strftime('%B %Y')}"


class InstitutionPaymentTracker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="payment_trackers"
    )
    student_fee_payment = models.ForeignKey(
        StudentFeePayment, on_delete=models.CASCADE, related_name="payment_trackers"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_disbursed = models.BooleanField(default=False)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution.name} - {self.amount} {'(Disbursed)' if self.is_disbursed else '(Pending)'}"
