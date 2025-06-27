from django.db import models
from uuid import uuid4
from institution.models import (
    InstitutionInfo,
    CurriculumTrack,
    Section,
    Subject,
    Module,
    Unit,
    Lesson,
    MicroLesson,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class Syllabus(models.Model):
    class PurposeChoices(models.TextChoices):
        YEARLY_EXAM = "yearly_exam", "Yearly Exam"
        HALF_YEARLY = "half_yearly", "Half Yearly"
        CLASS_TEST = "class_test", "Class Test"
        QUIZ = "quiz", "Quiz"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="syllabi"
    )
    curriculum_track = models.ForeignKey(
        CurriculumTrack, on_delete=models.CASCADE, related_name="syllabi"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="syllabi"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="syllabi"
    )
    title = models.CharField(max_length=200)
    purpose = models.CharField(
        max_length=20,
        choices=PurposeChoices.choices,
        default=PurposeChoices.YEARLY_EXAM,
    )
    modules = models.ManyToManyField(Module, blank=True, related_name="syllabi")
    units = models.ManyToManyField(Unit, blank=True, related_name="syllabi")
    lessons = models.ManyToManyField(Lesson, blank=True, related_name="syllabi")
    micro_lessons = models.ManyToManyField(
        MicroLesson, blank=True, related_name="syllabi"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_syllabi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Syllabus"
        verbose_name_plural = "Syllabus"
        indexes = [
            models.Index(
                fields=["institution", "curriculum_track", "section", "subject"]
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.subject} ({self.section})"
