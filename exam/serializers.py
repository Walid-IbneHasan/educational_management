from rest_framework import serializers
from .models import Exam, ExamMark, ExamType
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


class ExamSerializer(serializers.ModelSerializer):
    curriculum_track_id = serializers.UUIDField()
    section_id = serializers.UUIDField()
    subject_id = serializers.UUIDField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "curriculum_track_id",
            "section_id",
            "subject_id",
            "title",
            "exam_type",
            "exam_date",
            "total_marks",
            "is_active",
            "created_by",
        ]
        read_only_fields = ["created_by"]

    def validate(self, data):
        user = self.context["request"].user
        curriculum_track_id = data.get("curriculum_track_id")
        section_id = data.get("section_id")
        subject_id = data.get("subject_id")

        # Validate institution
        institution = user.memberships.filter(role="teacher").first().institution
        if not institution:
            logger.error(f"User {user.id} not associated with any institution")
            raise serializers.ValidationError(
                "User is not associated with an institution as a teacher."
            )

        # Validate curriculum track
        curriculum_track = CurriculumTrack.objects.filter(
            id=curriculum_track_id, institution_info=institution
        ).first()
        if not curriculum_track:
            logger.error(
                f"Curriculum track {curriculum_track_id} not found in institution {institution.id}"
            )
            raise serializers.ValidationError(
                f"Curriculum track ID {curriculum_track_id} does not exist or does not belong to your institution."
            )

        # Validate section
        section = Section.objects.filter(
            id=section_id, curriculum_track=curriculum_track
        ).first()
        if not section:
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

        # Check if subject is associated with the curriculum track via stream
        try:
            if subject.stream.curriculum_track != curriculum_track:
                logger.error(
                    f"Subject {subject_id} not linked to curriculum track {curriculum_track_id}"
                )
                raise serializers.ValidationError(
                    f"Subject ID {subject_id} is not part of the curriculum track."
                )
        except AttributeError as e:
            logger.error(f"Error accessing subject.stream.curriculum_track: {str(e)}")
            raise serializers.ValidationError(
                "Unable to validate subject-curriculum track relationship."
            )

        # Validate teacher enrollment
        if not TeacherEnrollment.objects.filter(
            user=user,
            curriculum_track=curriculum_track,
            section=section,
            subjects=subject,
            institution=institution,
        ).exists():
            logger.error(
                f"Teacher {user.id} not enrolled for subject {subject_id} in section {section_id}"
            )
            raise serializers.ValidationError(
                "You are not enrolled as a teacher for this subject in the specified section."
            )

        data["curriculum_track"] = curriculum_track
        data["section"] = section
        data["subject"] = subject
        return data

    def create(self, validated_data):
        curriculum_track = validated_data.pop("curriculum_track")
        section = validated_data.pop("section")
        subject = validated_data.pop("subject")
        validated_data.pop("curriculum_track_id")
        validated_data.pop("section_id")
        validated_data.pop("subject_id")
        return Exam.objects.create(
            curriculum_track=curriculum_track,
            section=section,
            subject=subject,
            created_by=self.context["request"].user,
            **validated_data,
        )


class ExamMarkSerializer(serializers.ModelSerializer):
    exam_id = serializers.UUIDField()
    student_id = serializers.UUIDField()

    class Meta:
        model = ExamMark
        fields = [
            "id",
            "exam_id",
            "student_id",
            "marks_obtained",
            "remarks",
        ]

    def validate(self, data):
        user = self.context["request"].user
        exam_id = data.get("exam_id")
        student_id = data.get("student_id")

        # Validate exam
        exam = Exam.objects.filter(id=exam_id).first()
        if not exam:
            logger.error(f"Exam {exam_id} not found")
            raise serializers.ValidationError(f"Exam ID {exam_id} does not exist.")

        # Validate institution
        institution = user.memberships.filter(role="teacher").first().institution
        if exam.curriculum_track.institution_info != institution:
            logger.error(f"Exam {exam_id} not in institution {institution.id}")
            raise serializers.ValidationError(
                "Exam does not belong to your institution."
            )

        # Validate teacher enrollment
        if not TeacherEnrollment.objects.filter(
            user=user,
            curriculum_track=exam.curriculum_track,
            section=exam.section,
            subjects=exam.subject,
            institution=institution,
        ).exists():
            logger.error(f"Teacher {user.id} not enrolled for exam {exam_id}")
            raise serializers.ValidationError(
                "You are not authorized to assign marks for this exam."
            )

        # Validate student
        student = User.objects.filter(id=student_id, is_student=True).first()
        if not student:
            logger.error(f"Student {student_id} not found")
            raise serializers.ValidationError(
                f"Student ID {student_id} does not exist."
            )

        # Validate student enrollment
        if not StudentEnrollment.objects.filter(
            user=student,
            curriculum_track=exam.curriculum_track,
            section=exam.section,
            is_active=True,
        ).exists():
            logger.error(
                f"Student {student_id} not enrolled in curriculum track {exam.curriculum_track.id} and section {exam.section.id}"
            )
            raise serializers.ValidationError(
                "Student is not enrolled in the specified curriculum track and section."
            )

        data["exam"] = exam
        data["student"] = student
        return data

    def create(self, validated_data):
        exam = validated_data.pop("exam")
        student = validated_data.pop("student")
        validated_data.pop("exam_id")
        validated_data.pop("student_id")
        return ExamMark.objects.create(
            exam=exam,
            student=student,
            **validated_data,
        )
