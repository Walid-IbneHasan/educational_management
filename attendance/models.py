import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from institution.models import InstitutionInfo, Section, Subject, StudentEnrollment


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendances",
        limit_choices_to={"is_student": True},
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
        ],
        default="present",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_attendances",
        limit_choices_to={"is_teacher": True},
    )

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        unique_together = ("student", "section", "subject", "date")
        indexes = [
            models.Index(fields=["institution", "date"]),
            models.Index(fields=["student", "date"]),
            models.Index(fields=["section", "subject", "date"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date} - {self.status}"

    def clean(self):

        # Ensure student is enrolled in the section
        if not StudentEnrollment.objects.filter(
            user=self.student,
            section=self.section,
            institution=self.institution,
            is_active=True,
        ).exists():
            raise ValidationError("Student is not enrolled in this section.")
        # Ensure subject belongs to the section's curriculum track
        if self.subject.stream.section != self.section:
            raise ValidationError("Subject does not belong to this section.")
