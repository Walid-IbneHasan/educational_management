from rest_framework import serializers
from django.db import transaction
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
    CurriculumTrack,
    Section,
    Stream,
    Subject,
    Module,
    Unit,
    Lesson,
    MicroLesson,
    InstitutionInfo,
    TeacherEnrollment,
    StudentEnrollment,
)
from user_management.models import ParentChildRelationship
import logging

logger = logging.getLogger(__name__)


class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ["id", "label", "text", "is_correct"]
        extra_kwargs = {"is_correct": {"write_only": True}}


class GlobalQuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizOptionSerializer(many=True, required=False)
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=GlobalCurriculumTrack.objects.all(), required=True
    )
    stream = serializers.PrimaryKeyRelatedField(
        queryset=GlobalStream.objects.all(), required=True
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=GlobalSubject.objects.all(), required=True
    )
    module = serializers.PrimaryKeyRelatedField(
        queryset=GlobalModule.objects.all(), required=True
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=GlobalUnit.objects.all(), required=True
    )
    lesson = serializers.PrimaryKeyRelatedField(
        queryset=GlobalLesson.objects.all(), required=False, allow_null=True
    )
    micro_lesson = serializers.PrimaryKeyRelatedField(
        queryset=GlobalMicroLesson.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = GlobalQuizQuestion
        fields = [
            "id",
            "curriculum_track",
            "stream",
            "subject",
            "module",
            "unit",
            "lesson",
            "micro_lesson",
            "question_type",
            "text",
            "image_url",
            "marks",
            "status",
            "options",
        ]

    def validate(self, data):
        if not (data.get("curriculum_track") and data.get("subject")):
            raise serializers.ValidationError(
                "Both curriculum_track and subject are required."
            )
        question_type = data.get("question_type", "mcq")
        options = data.get("options", [])
        if question_type == "mcq" and len(options) < 2:
            raise serializers.ValidationError(
                "MCQ questions must have at least 2 options."
            )
        if question_type == "true_false" and len(options) != 2:
            raise serializers.ValidationError(
                "True/False questions must have exactly 2 options."
            )
        if question_type == "short" and options:
            raise serializers.ValidationError(
                "Short answer questions cannot have options."
            )
        return data

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        question = GlobalQuizQuestion.objects.create(
            created_by=self.context["request"].user, **validated_data
        )
        for option_data in options_data:
            QuizOption.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        instance = super().update(instance, validated_data)
        if options_data is not None:
            instance.options.all().delete()
            for option_data in options_data:
                QuizOption.objects.create(question=instance, **option_data)
        return instance


class QuizContainerSerializer(serializers.ModelSerializer):
    curriculum_track_id = serializers.UUIDField()
    section_id = serializers.UUIDField(required=False, allow_null=True)
    stream_id = serializers.UUIDField(required=False, allow_null=True)
    subject_id = serializers.UUIDField()
    module_id = serializers.UUIDField(required=False, allow_null=True)
    unit_id = serializers.UUIDField(required=False, allow_null=True)
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    micro_lesson_id = serializers.UUIDField(required=False, allow_null=True)
    question_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=True
    )

    class Meta:
        model = QuizContainer
        fields = [
            "id",
            "title",
            "curriculum_track_id",
            "section_id",
            "stream_id",
            "subject_id",
            "module_id",
            "unit_id",
            "lesson_id",
            "micro_lesson_id",
            "start_time",
            "end_time",
            "timer_per_question",
            "enable_negative_marking",
            "negative_marks",
            "status",
            "is_free",
            "is_active",
            "order",
            "question_ids",
        ]

    def validate(self, data):
        curriculum_track_id = data.get("curriculum_track_id")
        section_id = data.get("section_id")
        stream_id = data.get("stream_id")
        subject_id = data.get("subject_id")
        module_id = data.get("module_id")
        unit_id = data.get("unit_id")
        lesson_id = data.get("lesson_id")
        micro_lesson_id = data.get("micro_lesson_id")
        question_ids = data.get("question_ids", [])
        user = self.context["request"].user

        logger.debug(
            f"Validating quiz creation for user {user.id}, curriculum_track_id: {curriculum_track_id}, subject_id: {subject_id}"
        )

        # Validate institution
        from user_management.models.authentication import InstitutionMembership

        institution = InstitutionInfo.objects.filter(
            memberships__user=user, memberships__role="teacher"
        ).first()
        if not institution:
            logger.error(
                f"User {user.id} not associated with any institution as a teacher"
            )
            raise serializers.ValidationError(
                "User is not associated with an institution as a teacher."
            )
        logger.debug(f"User {user.id} associated with institution {institution.id}")

        # Validate curriculum track
        curriculum_track = CurriculumTrack.objects.filter(
            id=curriculum_track_id, institution_info=institution
        ).first()
        if not curriculum_track:
            logger.error(
                f"Curriculum track {curriculum_track_id} not found or not in institution {institution.id}"
            )
            raise serializers.ValidationError(
                f"Curriculum track ID {curriculum_track_id} does not exist or does not belong to your institution."
            )

        # Validate section
        section = (
            Section.objects.filter(
                id=section_id, curriculum_track=curriculum_track
            ).first()
            if section_id
            else None
        )
        if section_id and not section:
            logger.error(
                f"Section {section_id} not found in curriculum track {curriculum_track_id}"
            )
            raise serializers.ValidationError(f"Invalid section ID {section_id}.")

        # Validate subject
        subject = Subject.objects.filter(id=subject_id).first()
        if not subject:
            logger.error(f"Subject {subject_id} not found")
            raise serializers.ValidationError(
                f"Subject ID {subject_id} does not exist."
            )
        if not Stream.objects.filter(
            curriculum_track=curriculum_track,
            subjects=subject,
        ).exists():
            logger.error(
                f"Subject {subject_id} not linked to any stream in curriculum track {curriculum_track_id}"
            )
            raise serializers.ValidationError(
                f"Subject ID {subject_id} is not part of the curriculum track {curriculum_track_id}."
            )

        # Validate teacher enrollment
        if user.is_teacher:
            enrollment = TeacherEnrollment.objects.filter(
                user=user,
                curriculum_track=curriculum_track,
                subjects=subject,
                institution=institution,
            ).first()
            if not enrollment:
                logger.error(
                    f"No TeacherEnrollment for user {user.id}, curriculum_track {curriculum_track_id}, subject {subject_id}, institution {institution.id}"
                )
                raise serializers.ValidationError(
                    f"You are not enrolled as a teacher for subject {subject_id} in curriculum track {curriculum_track_id}."
                )
            logger.debug(
                f"Teacher {user.id} enrolled for subject {subject_id} in curriculum track {curriculum_track_id}"
            )

        # Validate optional fields
        stream = (
            Stream.objects.filter(
                id=stream_id, curriculum_track=curriculum_track
            ).first()
            if stream_id
            else None
        )
        if stream_id and not stream:
            logger.error(
                f"Stream {stream_id} not found in curriculum track {curriculum_track_id}"
            )
            raise serializers.ValidationError(f"Invalid stream ID {stream_id}.")
        if stream and section and stream.section != section:
            logger.error(f"Stream {stream_id} does not belong to section {section_id}")
            raise serializers.ValidationError(
                f"Stream ID {stream_id} does not belong to section {section_id}."
            )

        module = (
            Module.objects.filter(id=module_id, subject=subject).first()
            if module_id
            else None
        )
        unit = (
            Unit.objects.filter(id=unit_id, module=module).first()
            if unit_id and module
            else None
        )
        lesson = (
            Lesson.objects.filter(id=lesson_id, unit=unit).first()
            if lesson_id and unit
            else None
        )
        micro_lesson = (
            MicroLesson.objects.filter(id=micro_lesson_id, lesson=lesson).first()
            if micro_lesson_id and lesson
            else None
        )

        if module_id and not module:
            logger.error(f"Module {module_id} not found for subject {subject_id}")
            raise serializers.ValidationError(f"Invalid module ID {module_id}.")
        if unit_id and not unit:
            logger.error(f"Unit {unit_id} not found for module {module_id}")
            raise serializers.ValidationError(f"Invalid unit ID {unit_id}.")
        if lesson_id and not lesson:
            logger.error(f"Lesson {lesson_id} not found for unit {unit_id}")
            raise serializers.ValidationError(f"Invalid lesson ID {lesson_id}.")
        if micro_lesson_id and not micro_lesson:
            logger.error(
                f"Micro lesson {micro_lesson_id} not found for lesson {lesson_id}"
            )
            raise serializers.ValidationError(
                f"Invalid micro lesson ID {micro_lesson_id}."
            )

        # Validate questions
        if not question_ids:
            logger.error("No question IDs provided")
            raise serializers.ValidationError("At least one question must be selected.")
        for question_id in question_ids:
            if not GlobalQuizQuestion.objects.filter(id=question_id).exists():
                logger.error(f"Question {question_id} not found")
                raise serializers.ValidationError(
                    f"Question ID {question_id} does not exist."
                )

        return data

    def create(self, validated_data):
        question_ids = validated_data.pop("question_ids", [])
        curriculum_track_id = validated_data.pop("curriculum_track_id")
        section_id = validated_data.pop("section_id", None)
        stream_id = validated_data.pop("stream_id", None)
        subject_id = validated_data.pop("subject_id")
        module_id = validated_data.pop("module_id", None)
        unit_id = validated_data.pop("unit_id", None)
        lesson_id = validated_data.pop("lesson_id", None)
        micro_lesson_id = validated_data.pop("micro_lesson_id", None)

        try:
            validated_data["curriculum_track"] = CurriculumTrack.objects.get(
                id=curriculum_track_id
            )
            validated_data["section"] = (
                Section.objects.get(id=section_id) if section_id else None
            )
            validated_data["subject"] = Subject.objects.get(id=subject_id)
            if stream_id:
                validated_data["stream"] = Stream.objects.get(id=stream_id)
            if module_id:
                validated_data["module"] = Module.objects.get(id=module_id)
            if unit_id:
                validated_data["unit"] = Unit.objects.get(id=unit_id)
            if lesson_id:
                validated_data["lesson"] = Lesson.objects.get(id=lesson_id)
            if micro_lesson_id:
                validated_data["micro_lesson"] = MicroLesson.objects.get(
                    id=micro_lesson_id
                )

            quiz = QuizContainer.objects.create(
                created_by=self.context["request"].user, **validated_data
            )
            quiz.questions.set(question_ids)
            logger.info(f"Quiz {quiz.id} created with questions {question_ids}")
            return quiz
        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
            raise serializers.ValidationError(f"Failed to create quiz: {str(e)}")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["question_ids"] = [str(q.id) for q in instance.questions.all()]
        return representation


class QuizResponseSerializer(serializers.ModelSerializer):
    question = GlobalQuizQuestionSerializer(read_only=True)
    selected_option = QuizOptionSerializer(read_only=True)

    class Meta:
        model = QuizResponse
        fields = [
            "id",
            "attempt",
            "question",
            "selected_option",
            "short_answer",
            "is_correct",
            "manual_score",
        ]
        read_only_fields = ["is_correct", "manual_score"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    responses = QuizResponseSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "user",
            "score",
            "started_at",
            "ended_at",
            "status",
            "responses",
        ]
        read_only_fields = ["score", "started_at", "ended_at", "status"]


class QuizAnswerSubmissionSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option = serializers.CharField(allow_blank=True, required=False)
    short_answer = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        try:
            question = GlobalQuizQuestion.objects.get(id=data["question_id"])
        except GlobalQuizQuestion.DoesNotExist:
            raise serializers.ValidationError("Invalid question ID.")
        question_type = question.question_type
        if question_type == "short" and not data.get("short_answer"):
            raise serializers.ValidationError(
                "Short answer is required for short answer questions."
            )
        if question_type in ["mcq", "true_false"] and not data.get("selected_option"):
            raise serializers.ValidationError(
                "Selected option is required for MCQ or True/False questions."
            )
        data["question"] = question
        return data


class QuizSubmissionSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    answers = QuizAnswerSubmissionSerializer(many=True)

    def validate_attempt_id(self, value):
        try:
            attempt = QuizAttempt.objects.select_related("quiz").get(
                id=value, user=self.context["request"].user
            )
        except QuizAttempt.DoesNotExist:
            raise serializers.ValidationError("Invalid attempt ID or not your attempt.")
        if attempt.status == "completed":
            raise serializers.ValidationError(
                "This quiz attempt has already been submitted."
            )
        self.context["attempt"] = attempt
        return value

    def create(self, validated_data):
        attempt = self.context["attempt"]
        quiz = attempt.quiz
        with transaction.atomic():
            for answer in validated_data["answers"]:
                question = answer["question"]
                is_correct = None
                if question.question_type == "short":
                    QuizResponse.objects.create(
                        attempt=attempt,
                        question=question,
                        short_answer=answer.get("short_answer"),
                        is_correct=None,
                    )
                else:
                    selected_label = answer.get("selected_option")
                    selected_option = QuizOption.objects.filter(
                        question=question, label=selected_label
                    ).first()
                    if not selected_option:
                        raise serializers.ValidationError(
                            f"Invalid option '{selected_label}' for question {question.id}."
                        )
                    is_correct = selected_option.is_correct
                    QuizResponse.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option,
                        is_correct=is_correct,
                    )
            attempt.complete_attempt()
        return {
            "attempt_id": attempt.id,
            "final_score": attempt.score,
            "submitted_at": attempt.ended_at,
        }


class ManualGradingSerializer(serializers.Serializer):
    response_id = serializers.UUIDField()
    manual_score = serializers.FloatField(min_value=0)

    def validate_response_id(self, value):
        try:
            response = QuizResponse.objects.select_related(
                "question", "attempt__quiz"
            ).get(id=value)
        except QuizResponse.DoesNotExist:
            raise serializers.ValidationError("Invalid response ID.")
        if response.question.question_type != "short":
            raise serializers.ValidationError(
                "Manual grading is only for short answer questions."
            )
        if response.attempt.quiz.created_by != self.context["request"].user:
            raise serializers.ValidationError(
                "You are not authorized to grade this response."
            )
        self.context["response"] = response
        return value

    def validate(self, data):
        response = self.context["response"]
        if data["manual_score"] > response.question.marks:
            raise serializers.ValidationError(
                f"Manual score cannot exceed question marks ({response.question.marks})."
            )
        return data

    def create(self, validated_data):
        response = self.context["response"]
        response.manual_score = validated_data["manual_score"]
        response.is_correct = validated_data["manual_score"] > 0
        response.save()
        attempt = response.attempt
        attempt.calculate_score()
        # Return a dictionary matching the serializer's fields
        return {"response_id": str(response.id), "manual_score": response.manual_score}

    def to_representation(self, instance):
        # Ensure the output matches the expected format
        return {
            "response_id": instance["response_id"],
            "manual_score": instance["manual_score"],
        }


class ParentQuizAttemptSerializer(serializers.ModelSerializer):
    child = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "child", "score", "started_at", "ended_at", "status"]

    def get_child(self, obj):
        return obj.user.username
