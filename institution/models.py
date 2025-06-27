from django.db import models
from uuid import uuid4
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone


# Common abstract model
class CommonFields(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Institution types as enum choices
class InstitutionType(models.TextChoices):
    PRE_CADET = "pre_cadet", "Pre-Cadet"
    KINDERGARTEN = "kindergarten", "Kindergarten"
    PRIMARY_SCHOOL = "primary_school", "Primary School"
    HIGH_SCHOOL = "high_school", "High School"
    HIGHER_SECONDARY = "higher_secondary", "Higher Secondary"
    UNIVERSITY = "university", "University"
    COACHING = "coaching", "Coaching Center"
    INDIVIDUAL = "individual", "Individual"
    OTHERS = "others", "Others"


# InstitutionInfo model
class InstitutionInfo(CommonFields):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    short_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    institution_type = models.CharField(
        max_length=30,
        choices=InstitutionType.choices,
        default=InstitutionType.PRIMARY_SCHOOL,
    )
    is_active = models.BooleanField(default=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institution_info",
    )

    class Meta:
        verbose_name = "Institution Information"
        verbose_name_plural = "Institution Information"

    def __str__(self):
        return self.name


# --------------------------------
#          Global Models
# --------------------------------


# Global Curriculum Track (Class / Program)
class GlobalCurriculumTrack(CommonFields):
    name = models.CharField(max_length=100, help_text="e.g., Class 9, BSc in CSE")
    description = models.TextField(
        blank=True, null=True, help_text="e.g., Description of Class 9"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Curriculum Track"
        verbose_name_plural = "Global Curriculum Tracks"

    def __str__(self):
        return self.name


# Global Stream / Group
class GlobalStream(CommonFields):
    name = models.CharField(
        max_length=100, help_text="# e.g., Science, Commerce, Major, Minor"
    )
    description = models.TextField(
        blank=True, null=True, help_text="e.g., Description of Science"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Stream"
        verbose_name_plural = "Global Streams"

    def __str__(self):
        return self.name


# Global Subject
class GlobalSubject(CommonFields):
    name = models.CharField(
        max_length=200, help_text="# e.g., Bangla First Paper, Math 101"
    )
    description = models.TextField(
        blank=True, null=True, help_text="e.g., Description of Bangla First Paper"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    code = models.CharField(
        max_length=50, blank=True, null=True, help_text="e.g., MTH101"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Subject"
        verbose_name_plural = "Global Subjects"

    def __str__(self):
        return self.name


# Global Module
class GlobalModule(CommonFields):
    title = models.CharField(max_length=200, help_text="e.g., Differential Calculus")
    description = models.TextField(
        blank=True, null=True, help_text="e.g., Module description"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Module"
        verbose_name_plural = "Global Modules"

    def __str__(self):
        return self.title


# Global Unit
class GlobalUnit(CommonFields):
    title = models.CharField(max_length=200, help_text="# e.g., Limits")
    description = models.TextField(
        blank=True, null=True, help_text="e.g., Unit description"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Unit"
        verbose_name_plural = "Global Units"

    def __str__(self):
        return self.title


# Global Lesson
class GlobalLesson(CommonFields):
    title = models.CharField(max_length=200, help_text="e.g., What is a Limit?")
    content = models.TextField(blank=True, null=True, help_text="e.g., Lesson content")
    video_url = models.URLField(
        blank=True, null=True, help_text="e.g., Youtube Video URL"
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Lesson"
        verbose_name_plural = "Global Lessons"

    def __str__(self):
        return self.title


# Global Micro Lesson
class GlobalMicroLesson(CommonFields):
    title = models.CharField(max_length=200, help_text="e.g., Micro lesson title")
    content_type = models.CharField(
        max_length=50,
        choices=[
            ("video", "Video"),
            ("quiz", "Quiz"),
            ("activity", "Activity"),
            ("text", "Text"),
        ],
    )
    institution_type = models.CharField(
        max_length=30, choices=InstitutionType.choices, blank=True, null=True
    )
    content = models.TextField(blank=True, null=True)
    video_url = models.URLField(
        blank=True, null=True, help_text="e.g., Youtube Video URL"
    )
    image_url = models.URLField(blank=True, null=True, help_text="e.g., Image URL")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Global Micro Lesson"
        verbose_name_plural = "Global Micro Lessons"

    def __str__(self):
        return self.title


# --------------------------------
#          Institution Models
# --------------------------------


# Curriculum Track
class CurriculumTrack(CommonFields):
    institution_info = models.ForeignKey(
        InstitutionInfo,
        on_delete=models.CASCADE,
        related_name="institution_curriculum_tracks",
    )
    name = models.ForeignKey(
        GlobalCurriculumTrack,
        on_delete=models.CASCADE,
        related_name="institution_curriculum_tracks_name",
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Curriculum Track"
        verbose_name_plural = "Curriculum Tracks"
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.institution_info})"


# Section
class Section(CommonFields):
    curriculum_track = models.ForeignKey(
        CurriculumTrack, on_delete=models.CASCADE, related_name="sections"
    )
    name = models.CharField(max_length=100, help_text="e.g., Section A, Section B")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ["order"]
        unique_together = ("curriculum_track", "name")

    def __str__(self):
        return f"{self.name} - {self.curriculum_track}"


# Stream / Group
class Stream(CommonFields):
    curriculum_track = models.ForeignKey(
        CurriculumTrack, on_delete=models.CASCADE, related_name="streams"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="streams", null=True, blank=True
    )
    name = models.ForeignKey(
        GlobalStream, on_delete=models.CASCADE, related_name="institution_streams"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Stream / Group"
        verbose_name_plural = "Streams / Groups"
        ordering = ["order"]

    def __str__(self):
        return (
            f"{self.name} - {self.section if self.section else self.curriculum_track}"
        )

    def clean(self):
        if self.section and self.section.curriculum_track != self.curriculum_track:
            raise ValidationError(
                "Section must belong to the specified curriculum track."
            )


# Subject
class Subject(CommonFields):
    stream = models.ForeignKey(
        Stream, on_delete=models.CASCADE, related_name="subjects"
    )
    name = models.ForeignKey(
        GlobalSubject, on_delete=models.CASCADE, related_name="subjects"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["order"]

    def __str__(self):
        return str(self.name)


# Module
class Module(CommonFields):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="modules"
    )
    title = models.ForeignKey(
        GlobalModule, on_delete=models.CASCADE, related_name="modules"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["order"]

    def __str__(self):
        return str(self.title)


# Unit
class Unit(CommonFields):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="units")
    title = models.ForeignKey(
        GlobalUnit, on_delete=models.CASCADE, related_name="units"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        ordering = ["order"]

    def __str__(self):
        return f"{self.module} > {self.title}"


# Lesson
class Lesson(CommonFields):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.ForeignKey(
        GlobalLesson, on_delete=models.CASCADE, related_name="lessons"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["order"]

    def __str__(self):
        return str(self.title)


# Micro Lesson
class MicroLesson(CommonFields):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="micro_lessons"
    )
    title = models.ForeignKey(
        GlobalMicroLesson, on_delete=models.CASCADE, related_name="micro_lessons"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Micro Lesson"
        verbose_name_plural = "Micro Lessons"
        ordering = ["order"]

    def __str__(self):
        return f"{self.lesson} > {self.title}"


# Teacher Enrollment
class TeacherEnrollment(CommonFields):
    institution = models.ForeignKey(
        InstitutionInfo,
        on_delete=models.CASCADE,
        related_name="teacher_enrollments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_enrollments",
    )
    curriculum_track = models.ManyToManyField(
        CurriculumTrack,
        related_name="teacher_enrollments",
    )
    section = models.ManyToManyField(
        Section,
        related_name="teacher_enrollments",
        blank=True,
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name="teacher_enrollments",
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Teacher Enrollment"
        verbose_name_plural = "Teacher Enrollments"

    def __str__(self):
        return f"{self.user} - {self.institution}"


# Student Enrollment
class StudentEnrollment(CommonFields):
    institution = models.ForeignKey(
        InstitutionInfo,
        on_delete=models.CASCADE,
        related_name="student_enrollments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_enrollments",
    )
    curriculum_track = models.ForeignKey(
        CurriculumTrack,
        on_delete=models.CASCADE,
        related_name="student_enrollments",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="student_enrollments",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Student Enrollment"
        verbose_name_plural = "Student Enrollments"
        unique_together = ("user", "curriculum_track", "section")
        indexes = [
            models.Index(fields=["user", "curriculum_track", "section"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.section}"

    def clean(self):
        if self.section.curriculum_track != self.curriculum_track:
            raise ValidationError(
                "Section must belong to the specified curriculum track."
            )























# Institution Fee (Default Monthly Fee)
class InstitutionFee(models.Model):
    institution = models.OneToOneField(
        InstitutionInfo, on_delete=models.CASCADE, related_name="default_fee"
    )
    default_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Default monthly fee for all students",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution.name} - Default Fee: {self.default_fee}"


class CurriculumTrackFee(models.Model):
    curriculum_track = models.OneToOneField(
        "CurriculumTrack", on_delete=models.CASCADE, related_name="fee"
    )
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Custom fee for this curriculum track",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.curriculum_track.name} - Fee: {self.fee}"


class StudentFee(models.Model):
    student_enrollment = models.OneToOneField(
        "StudentEnrollment", on_delete=models.CASCADE, related_name="fee"
    )
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Custom fee for this student",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_enrollment.user} - Fee: {self.fee}"
