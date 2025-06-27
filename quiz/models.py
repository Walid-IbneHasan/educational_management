from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from uuid import uuid4
from institution.models import *
from django.conf import settings


# --- Base and Choices ---
class CommonFields(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


STATUS_CHOICES = [
    ("draft", "Draft"),
    ("published", "Published"),
    ("archived", "Archived"),
]

QUESTION_TYPE_CHOICES = [
    ("mcq", "Multiple Choice"),
    ("true_false", "True/False"),
    ("short", "Short Answer"),
]


# --- Global Models ---
class GlobalQuizQuestion(CommonFields):
    curriculum_track = models.ForeignKey(
        GlobalCurriculumTrack,
        on_delete=models.CASCADE,
        related_name="quiz_questions_curriculum_track",
    )
    stream = models.ForeignKey(
        GlobalStream, on_delete=models.CASCADE, related_name="quiz_questions_stream"
    )
    subject = models.ForeignKey(
        GlobalSubject, on_delete=models.CASCADE, related_name="quiz_questions_subject"
    )
    module = models.ForeignKey(
        GlobalModule, on_delete=models.CASCADE, related_name="quiz_questions_module"
    )
    unit = models.ForeignKey(
        GlobalUnit, on_delete=models.CASCADE, related_name="quiz_questions_unit"
    )
    lesson = models.ForeignKey(
        GlobalLesson,
        on_delete=models.CASCADE,
        related_name="quiz_questions_lesson",
        blank=True,
        null=True,
    )
    micro_lesson = models.ForeignKey(
        GlobalMicroLesson,
        on_delete=models.CASCADE,
        related_name="quiz_questions_micro_lesson",
        blank=True,
        null=True,
    )
    question_type = models.CharField(
        max_length=50, choices=QUESTION_TYPE_CHOICES, default="mcq"
    )
    text = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    marks = models.FloatField(default=1.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_questions",
    )

    def __str__(self):
        return self.text[:60]

    class Meta:
        verbose_name = "Global Quiz Question"
        verbose_name_plural = "Global Quiz Questions"


class QuizOption(CommonFields):
    question = models.ForeignKey(
        GlobalQuizQuestion, on_delete=models.CASCADE, related_name="options"
    )
    label = models.CharField(
        max_length=1,
        choices=[
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            ("d", "D"),
            ("t", "True"),
            ("f", "False"),
        ],
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Quiz Option"
        verbose_name_plural = "Quiz Options"
        unique_together = ("question", "label")

    def __str__(self):
        return f"{self.label}: {self.text[:40]}"

    def clean(self):
        if self.question.question_type == "mcq" and self.is_correct:
            correct_options = QuizOption.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk)
            if correct_options.exists():
                raise ValidationError(
                    "Only one option can be marked as correct for MCQ questions."
                )
        if self.question.question_type == "true_false" and self.is_correct:
            correct_options = QuizOption.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk)
            if correct_options.exists():
                raise ValidationError(
                    "Only one option can be marked as correct for True/False questions."
                )


# --- Quiz Instance Models ---
class QuizContainer(CommonFields):
    curriculum_track = models.ForeignKey(
        CurriculumTrack,
        on_delete=models.CASCADE,
        related_name="quiz_container_curriculum_track",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="quiz_container_section",
        null=True,
        blank=True,
    )
    stream = models.ForeignKey(
        Stream,
        on_delete=models.CASCADE,
        related_name="quiz_container_stream",
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="quiz_container_subject"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="quiz_container_module",
        null=True,
        blank=True,
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="quiz_container_unit",
        null=True,
        blank=True,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quiz_container_lesson",
        blank=True,
        null=True,
    )
    micro_lesson = models.ForeignKey(
        MicroLesson,
        on_delete=models.CASCADE,
        related_name="quiz_container_micro_lesson",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    timer_per_question = models.PositiveIntegerField(null=True, blank=True)
    enable_negative_marking = models.BooleanField(default=False)
    negative_marks = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quizzes",
    )
    questions = models.ManyToManyField(
        GlobalQuizQuestion, related_name="quiz_containers"
    )

    def clean(self):
        if self.enable_negative_marking and (
            self.negative_marks is None or self.negative_marks <= 0
        ):
            raise ValidationError(
                "Negative marks must be > 0 if negative marking is enabled."
            )
        if (
            self.negative_marks
            and self.negative_marks > 0
            and not self.enable_negative_marking
        ):
            raise ValidationError(
                "Enable negative marking check box to add negative marks."
            )
        # Validate curriculum hierarchy
        if not Stream.objects.filter(
            curriculum_track=self.curriculum_track, subjects=self.subject
        ).exists():
            raise ValidationError(
                "Subject does not belong to the specified curriculum track."
            )
        if self.section and self.section.curriculum_track != self.curriculum_track:
            raise ValidationError(
                "Section does not belong to the specified curriculum track."
            )
        if self.stream and self.stream.curriculum_track != self.curriculum_track:
            raise ValidationError(
                "Stream does not belong to the specified curriculum track."
            )
        if self.stream and self.section and self.stream.section != self.section:
            raise ValidationError("Stream does not belong to the specified section.")
        if self.module and self.module.subject != self.subject:
            raise ValidationError("Module does not belong to the specified subject.")
        if self.unit and self.unit.module != self.module:
            raise ValidationError("Unit does not belong to the specified module.")
        if self.lesson and self.lesson.unit != self.unit:
            raise ValidationError("Lesson does not belong to the specified unit.")
        if self.micro_lesson and self.micro_lesson.lesson != self.lesson:
            raise ValidationError(
                "Micro lesson does not belong to the specified lesson."
            )

    def __str__(self):
        return self.title


# --- Quiz Attempt and Response Models ---
ATTEMPT_STATUS_CHOICES = [
    ("started", "Started"),
    ("completed", "Completed"),
]


class QuizAttempt(CommonFields):
    quiz = models.ForeignKey(
        QuizContainer, on_delete=models.CASCADE, related_name="attempts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    score = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=ATTEMPT_STATUS_CHOICES, default="started"
    )

    def __str__(self):
        return f"{self.user}'s attempt on {self.quiz.title} ({self.status})"

    def calculate_score(self):
        total_score = 0
        responses = self.responses.select_related("question", "selected_option").all()
        for response in responses:
            question = response.question
            if response.manual_score is not None:
                total_score += response.manual_score
            elif response.is_correct is True:
                total_score += question.marks
            elif response.is_correct is False and self.quiz.enable_negative_marking:
                total_score -= self.quiz.negative_marks or 0
        self.score = max(0, total_score)
        self.save(update_fields=["score"])

    def complete_attempt(self):
        if self.status == "started":
            self.ended_at = timezone.now()
            self.status = "completed"
            self.save(update_fields=["ended_at", "status"])
            self.calculate_score()


class QuizResponse(CommonFields):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(
        GlobalQuizQuestion, on_delete=models.CASCADE, related_name="responses"
    )
    selected_option = models.ForeignKey(
        QuizOption, on_delete=models.SET_NULL, null=True, blank=True
    )
    short_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)
    manual_score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"Response for {self.question.text[:20]}... in attempt {self.attempt.id}"

    def clean(self):
        q_type = self.question.question_type
        if q_type in ["mcq", "true_false"]:
            if self.selected_option is None and self.short_answer:
                raise ValidationError(
                    f"Do not provide short answer for {q_type} questions."
                )
            if self.selected_option and self.selected_option.question != self.question:
                raise ValidationError(
                    "The selected option does not belong to this question."
                )
        elif q_type == "short":
            if self.selected_option is not None:
                raise ValidationError(
                    "Do not select an option for short answer questions."
                )

    def save(self, *args, **kwargs):
        if self.is_correct is None:
            q_type = self.question.question_type
            if q_type in ["mcq", "true_false"]:
                self.is_correct = (
                    self.selected_option.is_correct if self.selected_option else False
                )
            elif q_type == "short":
                self.is_correct = None
        super().save(*args, **kwargs)
