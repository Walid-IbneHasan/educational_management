from django.db import models
from user_management.models.authentication import User
from institution.models import InstitutionInfo
import uuid


class AdmissionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        related_name="admission_requests",
        on_delete=models.CASCADE,
        help_text="The user requesting admission.",
    )
    institution = models.ForeignKey(
        InstitutionInfo,
        related_name="admission_requests",
        on_delete=models.CASCADE,
        help_text="The institution to which the user is requesting admission.",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
        help_text="The status of the admission request.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The date and time the request was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="The date and time the request was last updated."
    )

    class Meta:
        unique_together = ["user", "institution"]
        verbose_name = "Admission Request"
        verbose_name_plural = "Admission Requests"

    def __str__(self):
        return f"{self.user.email or self.user.phone_number} -> {self.institution.name} ({self.status})"
