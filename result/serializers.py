from rest_framework import serializers
from quiz.models import QuizAttempt
from exam.models import ExamMark
from institution.models import (
    CurriculumTrack,
    Section,
    Subject,
    TeacherEnrollment,
    StudentEnrollment,
)
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class QuizResultSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    subject = serializers.CharField(source="quiz.subject.name.name", read_only=True)
    curriculum_track = serializers.CharField(
        source="quiz.curriculum_track.name.name", read_only=True
    )
    section = serializers.CharField(
        source="quiz.section.name", read_only=True, allow_null=True
    )

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz_title",
            "subject",
            "curriculum_track",
            "section",
            "score",
            "started_at",
            "ended_at",
            "status",
        ]


class ExamResultSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    subject = serializers.CharField(source="exam.subject.name.name", read_only=True)
    curriculum_track = serializers.CharField(
        source="exam.curriculum_track.name.name", read_only=True
    )
    section = serializers.CharField(source="exam.section.name", read_only=True)
    exam_type = serializers.CharField(source="exam.exam_type", read_only=True)
    exam_date = serializers.DateField(source="exam.exam_date", read_only=True)

    class Meta:
        model = ExamMark
        fields = [
            "id",
            "exam_title",
            "subject",
            "curriculum_track",
            "section",
            "exam_type",
            "exam_date",
            "marks_obtained",
            "remarks",
        ]


class StudentResultSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    quiz_results = QuizResultSerializer(many=True, read_only=True)
    exam_results = ExamResultSerializer(many=True, read_only=True)

    def validate_student_id(self, value):
        user = self.context["request"].user
        student = User.objects.filter(id=value, is_student=True).first()
        if not student:
            logger.error(f"Student {value} not found")
            raise serializers.ValidationError(f"Student ID {value} does not exist.")

        # Validate access
        institution = user.memberships.first().institution
        if user.is_teacher:
            if not TeacherEnrollment.objects.filter(
                user=user,
                curriculum_track__student_enrollments__user=student,
                section__student_enrollments__user=student,
                institution=institution,
            ).exists():
                logger.error(
                    f"Teacher {user.id} not authorized to view results for student {value}"
                )
                raise serializers.ValidationError(
                    "You are not authorized to view results for this student."
                )
        elif user.is_student and user.id != value:
            logger.error(
                f"Student {user.id} attempted to view results for another student {value}"
            )
            raise serializers.ValidationError("You can only view your own results.")
        return value

    def to_representation(self, instance):
        student_id = instance["student_id"]
        institution = self.context["request"].user.memberships.first().institution

        # Log quiz attempt query details for debugging
        quiz_attempts = QuizAttempt.objects.filter(
            user__id=student_id,
            quiz__curriculum_track__institution_info=institution,
            status="completed",
        )
        logger.debug(
            f"Quiz attempts found for student {student_id}: {quiz_attempts.count()}"
        )
        for attempt in quiz_attempts:
            logger.debug(
                f"Attempt: {attempt.id}, Status: {attempt.status}, Quiz: {attempt.quiz.title}"
            )

        quiz_results = quiz_attempts
        exam_results = ExamMark.objects.filter(
            student__id=student_id,
            exam__curriculum_track__institution_info=institution,
        )

        return {
            "student_id": str(student_id),
            "quiz_results": QuizResultSerializer(quiz_results, many=True).data,
            "exam_results": ExamResultSerializer(exam_results, many=True).data,
        }


class SectionResultSerializer(serializers.Serializer):
    section_id = serializers.UUIDField(required=True)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    student_id = serializers.UUIDField(required=False, allow_null=True)
    students = serializers.ListField(child=serializers.DictField(), read_only=True)

    def validate(self, data):
        user = self.context["request"].user
        section_id = data.get("section_id")
        subject_id = data.get("subject_id")
        student_id = data.get("student_id")

        if not user.is_teacher:
            logger.error(
                f"Non-teacher user {user.id} attempted to access section results"
            )
            raise serializers.ValidationError(
                "Only teachers can access section results."
            )

        institution = user.memberships.filter(role="teacher").first().institution
        if not institution:
            logger.error(f"Teacher {user.id} not associated with any institution")
            raise serializers.ValidationError(
                "You are not associated with an institution."
            )

        # Validate section
        section = Section.objects.filter(id=section_id).first()
        if not section or section.curriculum_track.institution_info != institution:
            logger.error(
                f"Section {section_id} not found or not in institution {institution.id}"
            )
            raise serializers.ValidationError(
                f"Section ID {section_id} is invalid or not in your institution."
            )

        # Validate subject if provided
        if subject_id:
            subject = Subject.objects.filter(id=subject_id).first()
            if (
                not subject
                or subject.stream.curriculum_track != section.curriculum_track
            ):
                logger.error(
                    f"Subject {subject_id} not found or not in curriculum track {section.curriculum_track.id}"
                )
                raise serializers.ValidationError(
                    f"Subject ID {subject_id} is invalid or not in the curriculum track."
                )

        # Validate student if provided
        if student_id:
            student = User.objects.filter(id=student_id, is_student=True).first()
            if (
                not student
                or not StudentEnrollment.objects.filter(
                    user=student, section=section, is_active=True
                ).exists()
            ):
                logger.error(
                    f"Student {student_id} not found or not enrolled in section {section_id}"
                )
                raise serializers.ValidationError(
                    f"Student ID {student_id} is invalid or not enrolled in the section."
                )

        # Validate teacher enrollment
        teacher_enrollment = TeacherEnrollment.objects.filter(
            user=user,
            section=section,
            institution=institution,
        )
        if subject_id:
            teacher_enrollment = teacher_enrollment.filter(subjects__id=subject_id)
        if not teacher_enrollment.exists():
            logger.error(
                f"Teacher {user.id} not enrolled in section {section_id} or subject {subject_id}"
            )
            raise serializers.ValidationError(
                "You are not enrolled as a teacher for this section or subject."
            )

        data["section"] = section
        data["subject"] = subject if subject_id else None
        data["student"] = student if student_id else None
        return data

    def to_representation(self, instance):
        section = instance["section"]
        subject = instance.get("subject")
        student = instance.get("student")
        institution = self.context["request"].user.memberships.first().institution

        # Get students in the section
        students = User.objects.filter(
            student_enrollments__section=section,
            student_enrollments__is_active=True,
            is_student=True,
        )
        if student:
            students = students.filter(id=student.id)

        result = []
        for student in students:
            quiz_results = QuizAttempt.objects.filter(
                user=student,
                quiz__curriculum_track__institution_info=institution,
                quiz__section=section,
                status="completed",
            )
            if subject:
                quiz_results = quiz_results.filter(quiz__subject=subject)

            exam_results = ExamMark.objects.filter(
                student=student,
                exam__curriculum_track__institution_info=institution,
                exam__section=section,
            )
            if subject:
                exam_results = exam_results.filter(exam__subject=subject)

            result.append(
                {
                    "student_id": str(student.id),
                    "student_name": f"{student.first_name} {student.last_name}",
                    "quiz_results": QuizResultSerializer(quiz_results, many=True).data,
                    "exam_results": ExamResultSerializer(exam_results, many=True).data,
                }
            )

        return {
            "section_id": str(section.id),
            "subject_id": str(subject.id) if subject else None,
            "student_id": str(student.id) if student else None,
            "students": result,
        }
