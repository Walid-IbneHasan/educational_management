from django.db import models
from uuid import uuid4
from institution.models import InstitutionInfo, CurriculumTrack, Section, Subject
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Homework(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="homeworks"
    )
    curriculum_track = models.ForeignKey(
        CurriculumTrack, on_delete=models.CASCADE, related_name="homeworks"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="homeworks"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="homeworks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="homework_images/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
    )
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_homeworks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Homework"
        verbose_name_plural = "Homeworks"
        indexes = [
            models.Index(
                fields=["institution", "curriculum_track", "section", "subject"]
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.subject} ({self.section})"


class HomeworkSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    homework = models.ForeignKey(
        Homework, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="homework_submissions"
    )
    submitted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="updated_submissions"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homework Submission"
        verbose_name_plural = "Homework Submissions"
        unique_together = ["homework", "student"]
        indexes = [
            models.Index(fields=["homework", "student"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.homework} ({'Submitted' if self.submitted else 'Not Submitted'})"
