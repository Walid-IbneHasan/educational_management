from django.db import models
from uuid import uuid4
from institution.models import InstitutionInfo
from django.contrib.auth import get_user_model

User = get_user_model()


class NoticeTargetAudience(models.TextChoices):
    STUDENTS = "students", "Students"
    TEACHERS = "teachers", "Teachers"
    PARENTS = "parents", "Parents"
    ALL = "all", "All"


class NoticeType(models.TextChoices):
    GENERAL = "general", "General"
    URGENT = "urgent", "Urgent"
    EVENT = "event", "Event"
    ANNOUNCEMENT = "announcement", "Announcement"
    ALERT = "alert", "Alert"


class Notice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="notices"
    )
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True, help_text="Content of the notice")
    target_audience = models.CharField(
        max_length=20,
        choices=NoticeTargetAudience.choices,
        default=NoticeTargetAudience.ALL,
        help_text="Target audience for the notice",
    )
    notice_type = models.CharField(
        max_length=20,
        choices=NoticeType.choices,
        default=NoticeType.GENERAL,
        help_text="Type of the notice",
    )
    image = models.ImageField(
        upload_to="notices/images/",
        null=True,
        blank=True,
        help_text="Optional image for the notice",
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_notices"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notice"
        verbose_name_plural = "Notices"
        indexes = [
            models.Index(fields=["institution", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.institution}"
