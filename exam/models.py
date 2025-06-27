from django.db import models
from uuid import uuid4
from django.conf import settings
from institution.models import CurriculumTrack, Section, Subject, StudentEnrollment
from django.core.exceptions import ValidationError
from django.utils import timezone


class CommonFields(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ExamType(models.TextChoices):
    MIDTERM = "midterm", "Midterm"
    FINAL = "final", "Final"
    CLASS_TEST = "class_test", "Class Test"
    OTHER = "other", "Other"


class Exam(CommonFields):
    curriculum_track = models.ForeignKey(
        CurriculumTrack,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    title = models.CharField(max_length=255)
    exam_type = models.CharField(
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.CLASS_TEST,
    )
    exam_date = models.DateField()
    total_marks = models.FloatField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_exams",
    )

    class Meta:
        verbose_name = "Exam"
        verbose_name_plural = "Exams"
        indexes = [
            models.Index(fields=["curriculum_track", "section", "subject"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.subject} ({self.exam_date})"

    def clean(self):
        if self.section.curriculum_track != self.curriculum_track:
            raise ValidationError(
                "Section must belong to the specified curriculum track."
            )
        try:
            if self.subject.stream.curriculum_track != self.curriculum_track:
                raise ValidationError(
                    "Subject does not belong to the specified curriculum track."
                )
        except AttributeError:
            raise ValidationError(
                "Unable to validate subject-curriculum track relationship."
            )
        if self.exam_date > timezone.now().date():
            raise ValidationError("Exam date cannot be in the future.")


class ExamMark(CommonFields):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="marks",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_marks",
    )
    marks_obtained = models.FloatField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Exam Mark"
        verbose_name_plural = "Exam Marks"
        unique_together = ("exam", "student")
        indexes = [
            models.Index(fields=["exam", "student"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.exam} ({self.marks_obtained})"

    def clean(self):
        if self.marks_obtained > self.exam.total_marks:
            raise ValidationError(
                f"Marks obtained cannot exceed total marks ({self.exam.total_marks})."
            )
        if self.marks_obtained < 0:
            raise ValidationError("Marks obtained cannot be negative.")
        # Validate student enrollment
        if not StudentEnrollment.objects.filter(
            user=self.student,
            curriculum_track=self.exam.curriculum_track,
            section=self.exam.section,
            is_active=True,
        ).exists():
            raise ValidationError(
                "Student is not enrolled in the specified curriculum track and section."
            )
