from rest_framework import serializers
from user_management.serializers.authentication import UserSerializer
from .models import Homework, HomeworkSubmission
from institution.models import InstitutionInfo, CurriculumTrack, Section, Subject
from django.utils import timezone


from django.contrib.auth import get_user_model

User = get_user_model()


class HomeworkSerializer(serializers.ModelSerializer):
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())

    class Meta:
        model = Homework
        fields = [
            "id",
            "institution",
            "curriculum_track",
            "section",
            "subject",
            "title",
            "description",
            "image",
            "due_date",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "institution", "created_at", "updated_at"]

    def validate(self, data):
        request = self.context["request"]
        curriculum_track = data.get("curriculum_track")
        section = data.get("section")
        subject = data.get("subject")
        due_date = data.get("due_date")

        # Validate teacher role
        if not request.user.is_teacher:
            raise serializers.ValidationError(
                {"non_field_errors": "Only teachers can create or update homework."}
            )

        # Validate institution
        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=curriculum_track
        ).first()
        if not institution:
            raise serializers.ValidationError(
                {"curriculum_track": "Invalid curriculum track."}
            )

        # Validate section belongs to curriculum track
        if section.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "section": "Section does not belong to the specified curriculum track."
                }
            )

        # Validate subject belongs to curriculum track
        if subject.stream.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "subject": "Subject does not belong to the specified curriculum track."
                }
            )

        # Validate teacher enrollment
        if not request.user.teacher_enrollments.filter(
            institution=institution,
            curriculum_track=curriculum_track,
            section=section,
            subjects=subject,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not enrolled to teach this subject in this section."
                }
            )

        # Validate due date
        if due_date <= timezone.now():
            raise serializers.ValidationError(
                {"due_date": "Due date must be in the future."}
            )

        return data

    def create(self, validated_data):
        curriculum_track = validated_data.get("curriculum_track")
        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=curriculum_track
        ).first()
        validated_data["institution"] = institution
        validated_data["created_by"] = self.context["request"].user
        return Homework.objects.create(**validated_data)


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_student=True), write_only=True, source="student"
    )
    homework_id = serializers.PrimaryKeyRelatedField(
        queryset=Homework.objects.all(), write_only=True, source="homework"
    )

    class Meta:
        model = HomeworkSubmission
        fields = [
            "id",
            "homework",
            "homework_id",
            "student",
            "student_id",
            "submitted",
            "submission_date",
            "updated_at",
        ]
        read_only_fields = ["id", "homework", "student", "updated_at"]

    def validate(self, data):
        request = self.context["request"]
        homework = data.get("homework")
        student = data.get("student")
        submitted = data.get("submitted", False)

        # Validate teacher role
        if not request.user.is_teacher:
            raise serializers.ValidationError(
                {"non_field_errors": "Only teachers can update submissions."}
            )

        # Validate teacher is assigned to homework's section and subject
        if not request.user.teacher_enrollments.filter(
            institution=homework.institution,
            curriculum_track=homework.curriculum_track,
            section=homework.section,
            subjects=homework.subject,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not authorized to update submissions for this homework."
                }
            )

        # Validate student is enrolled in the section
        if not student.student_enrollments.filter(
            institution=homework.institution,
            curriculum_track=homework.curriculum_track,
            section=homework.section,
        ).exists():
            raise serializers.ValidationError(
                {"student": "Student is not enrolled in this section."}
            )

        # Set submission date if submitted
        if submitted and not data.get("submission_date"):
            data["submission_date"] = timezone.now()
        elif not submitted:
            data["submission_date"] = None

        return data

    def create(self, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return HomeworkSubmission.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class HomeworkStatisticsSerializer(serializers.Serializer):
    student = UserSerializer()
    total_homeworks = serializers.IntegerField()
    submitted = serializers.IntegerField()
    not_submitted = serializers.IntegerField()
