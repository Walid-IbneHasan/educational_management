from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
import logging
from .models import (
    GlobalQuizQuestion,
    QuizOption,
    QuizContainer,
    QuizAttempt,
    QuizResponse,
)
from institution.models import (
    GlobalCurriculumTrack,
    GlobalStream,
    GlobalSubject,
    GlobalModule,
    GlobalUnit,
    GlobalLesson,
    GlobalMicroLesson,
)

logger = logging.getLogger(__name__)


class QuizOptionInlineForm(forms.ModelForm):
    class Meta:
        model = QuizOption
        fields = ["label", "text", "is_correct", "question"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When creating a new GlobalQuizQuestion, set question queryset to empty
        if not self.instance.pk and not self.initial.get("question"):
            self.fields["question"].queryset = GlobalQuizQuestion.objects.none()


class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    form = QuizOptionInlineForm
    extra = 4
    fields = ["label", "text", "is_correct"]
    readonly_fields = ["created_at", "updated_at"]


class QuizResponseInline(admin.TabularInline):
    model = QuizResponse
    extra = 0
    fields = [
        "question",
        "selected_option",
        "short_answer",
        "is_correct",
        "manual_score",
    ]
    readonly_fields = ["created_at", "updated_at"]


class GlobalQuizQuestionForm(forms.ModelForm):
    class Meta:
        model = GlobalQuizQuestion
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Set static querysets for all ForeignKey fields
            self.fields["curriculum_track"].queryset = (
                GlobalCurriculumTrack.objects.all()
            )
            self.fields["stream"].queryset = GlobalStream.objects.all()
            self.fields["subject"].queryset = GlobalSubject.objects.all()
            self.fields["module"].queryset = GlobalModule.objects.all()
            self.fields["unit"].queryset = GlobalUnit.objects.all()
            self.fields["lesson"].queryset = GlobalLesson.objects.all()
            self.fields["micro_lesson"].queryset = GlobalMicroLesson.objects.all()
        except Exception as e:
            logger.error(
                f"Error initializing GlobalQuizQuestionForm querysets: {str(e)}"
            )
            raise

    def clean(self):
        cleaned_data = super().clean()
        curriculum_track = cleaned_data.get("curriculum_track")
        stream = cleaned_data.get("stream")
        subject = cleaned_data.get("subject")
        module = cleaned_data.get("module")
        unit = cleaned_data.get("unit")
        lesson = cleaned_data.get("lesson")
        micro_lesson = cleaned_data.get("micro_lesson")

        # Log cleaned data for debugging
        logger.debug(f"Cleaning form data: {cleaned_data}")

        # Basic validation to ensure relationships are consistent
        try:
            if stream and curriculum_track:
                if not GlobalStream.objects.filter(
                    id=stream.id, institution_type=curriculum_track.institution_type
                ).exists():
                    raise ValidationError(
                        "Stream must belong to the same institution type as the curriculum track."
                    )
            if module and subject:
                if not GlobalModule.objects.filter(
                    id=module.id, institution_type=subject.institution_type
                ).exists():
                    raise ValidationError(
                        "Module must belong to the same institution type as the subject."
                    )
            if unit and module:
                if not GlobalUnit.objects.filter(
                    id=unit.id, institution_type=module.institution_type
                ).exists():
                    raise ValidationError(
                        "Unit must belong to the same institution type as the module."
                    )
            if lesson and unit:
                if not GlobalLesson.objects.filter(
                    id=lesson.id, institution_type=unit.institution_type
                ).exists():
                    raise ValidationError(
                        "Lesson must belong to the same institution type as the unit."
                    )
            if micro_lesson and lesson:
                if not GlobalMicroLesson.objects.filter(
                    id=micro_lesson.id, institution_type=lesson.institution_type
                ).exists():
                    raise ValidationError(
                        "Micro lesson must belong to the same institution type as the lesson."
                    )
        except Exception as e:
            logger.error(f"Error in GlobalQuizQuestionForm.clean: {str(e)}")
            raise ValidationError(f"Validation error: {str(e)}")

        return cleaned_data


@admin.register(GlobalQuizQuestion)
class GlobalQuizQuestionAdmin(admin.ModelAdmin):
    form = GlobalQuizQuestionForm
    list_display = (
        "text",
        "question_type",
        "curriculum_track",
        "stream",
        "subject",
        "module",
        "unit",
        "status",
    )
    list_filter = ("question_type", "status", "curriculum_track", "stream", "subject")
    search_fields = ("text",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [QuizOptionInline]

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving GlobalQuizQuestion: {str(e)}")
            raise


@admin.register(QuizOption)
class QuizOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "label", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(QuizContainer)
class QuizContainerAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "curriculum_track",
        "stream",
        "subject",
        "module",
        "status",
        "created_by",
    )
    list_filter = ("status", "is_active", "curriculum_track", "stream", "subject")
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("quiz", "user", "score", "status", "started_at", "ended_at")
    list_filter = ("status", "quiz")
    search_fields = ("user__username", "quiz__title")
    readonly_fields = ("created_at", "updated_at")
    inlines = [QuizResponseInline]


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "manual_score")
    list_filter = ("is_correct",)
    search_fields = ("question__text",)
    readonly_fields = ("created_at", "updated_at")
