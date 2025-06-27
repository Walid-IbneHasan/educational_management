from django.db import models
from uuid import uuid4
from institution.models import InstitutionInfo, StudentEnrollment
from django.core.validators import MinValueValidator, MaxValueValidator


class Scholarship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="scholarships"
    )
    student_enrollment = models.ForeignKey(
        StudentEnrollment, on_delete=models.CASCADE, related_name="scholarships"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Scholarship percentage (0-100)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("institution", "student_enrollment")
        verbose_name = "Scholarship"
        verbose_name_plural = "Scholarships"

    def __str__(self):
        return f"{self.student_enrollment.user} - {self.percentage}%"
