import uuid
from rest_framework import serializers
from .models import Attendance
from institution.models import InstitutionInfo, Section, Subject
from user_management.models.authentication import User, ParentChildRelationship
from django.db.models import Q
from datetime import date


class AttendanceSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Attendance
        fields = (
            "id",
            "institution",
            "student",
            "section",
            "section_name",
            "subject",
            "subject_name",
            "date",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "created_by")

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        institution = data.get("institution")
        student = data.get("student")
        section = data.get("section")
        subject = data.get("subject")
        date = data.get("date")

        # Ensure user is a teacher in the institution
        if (
            not user.is_teacher
            or not user.memberships.filter(
                institution=institution, role="teacher"
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not authorized to manage attendance for this institution."
                }
            )

        # Validate teacher enrollment
        if not user.teacher_enrollments.filter(
            institution=institution, section=section, subjects=subject, is_active=True
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not enrolled to teach this subject in this section."
                }
            )

        # Validate student enrollment
        if not student.student_enrollments.filter(
            institution=institution, section=section, is_active=True
        ).exists():
            raise serializers.ValidationError(
                {"student": "Student is not enrolled in this section."}
            )

        # Validate date
        if date > date.today():
            raise serializers.ValidationError(
                {"date": "Cannot record attendance for a future date."}
            )

        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class BulkAttendanceSerializer(serializers.Serializer):
    institution = serializers.PrimaryKeyRelatedField(
        queryset=InstitutionInfo.objects.all()
    )
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    date = serializers.DateField()
    attendances = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=True,
        ),
        allow_empty=False,
    )

    def validate_attendances(self, value):
        valid_statuses = ["present", "absent", "late", "excused"]
        for att in value:
            if (
                not isinstance(att, dict)
                or "student_id" not in att
                or "status" not in att
            ):
                raise serializers.ValidationError(
                    "Each attendance must have 'student_id' and 'status'."
                )
            if att["status"] not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status '{att['status']}'. Valid statuses are: {', '.join(valid_statuses)}."
                )
            try:
                uuid.UUID(att["student_id"])
            except ValueError:
                raise serializers.ValidationError(
                    f"Invalid UUID for student_id: {att['student_id']}."
                )
        return value

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        institution = data.get("institution")
        section = data.get("section")
        subject = data.get("subject")
        date = data.get("date")

        # Teacher authorization
        if (
            not user.is_teacher
            or not user.memberships.filter(
                institution=institution, role="teacher"
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not authorized to manage attendance for this institution."
                }
            )

        # Teacher enrollment
        if not user.teacher_enrollments.filter(
            institution=institution, section=section, subjects=subject, is_active=True
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not enrolled to teach this subject in this section."
                }
            )

        # Validate date
        if date > date.today():
            raise serializers.ValidationError(
                {"date": "Cannot record attendance for a future date."}
            )

        # Validate students
        student_ids = [att["student_id"] for att in data["attendances"]]
        valid_students = User.objects.filter(
            id__in=student_ids,
            is_student=True,
            student_enrollments__institution=institution,
            student_enrollments__section=section,
            student_enrollments__is_active=True,
        ).values_list("id", flat=True)
        invalid_students = set(student_ids) - set(str(id) for id in valid_students)
        if invalid_students:
            raise serializers.ValidationError(
                {
                    "attendances": f"Invalid or unenrolled student IDs: {', '.join(invalid_students)}"
                }
            )

        return data


class StudentAttendanceSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)
    subject_name = serializers.CharField(
        source="subject.name", read_only=True
    )  # Changed from subject.name.name

    class Meta:
        model = Attendance
        fields = (
            "id",
            "section",
            "section_name",
            "subject",
            "subject_name",
            "date",
            "status",
            "created_at",
        )
        read_only_fields = fields


class AttendanceStatisticsSerializer(serializers.Serializer):
    student_id = serializers.UUIDField(source="student__id")
    student_name = serializers.CharField(source="student__first_name")
    section_name = serializers.CharField(source="section__name", allow_null=True)
    subject_name = serializers.CharField(source="subject__name", allow_null=True)
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()

    class Meta:
        fields = (
            "student_id",
            "student_name",
            "section_name",
            "subject_name",
            "present_count",
            "absent_count",
            "late_count",
            "excused_count",
        )
