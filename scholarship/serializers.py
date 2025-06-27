from rest_framework import serializers
from .models import Scholarship
from institution.models import InstitutionInfo, StudentEnrollment
from institution.serializers import StudentEnrollmentSerializer


class ScholarshipSerializer(serializers.ModelSerializer):
    student_enrollment = StudentEnrollmentSerializer(read_only=True)
    student_enrollment_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Scholarship
        fields = [
            "id",
            "institution",
            "student_enrollment",
            "student_enrollment_id",
            "percentage",
            "is_active",
        ]
        read_only_fields = ["institution"]

    def validate(self, data):
        institution = self.context.get("institution")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )

        student_enrollment = StudentEnrollment.objects.filter(
            id=data.get("student_enrollment_id"), institution=institution
        ).first()

        if not student_enrollment:
            raise serializers.ValidationError(
                {
                    "student_enrollment_id": "Invalid student enrollment or does not belong to this institution."
                }
            )

        return data

    def create(self, validated_data):
        validated_data["institution"] = self.context["institution"]
        validated_data["student_enrollment"] = StudentEnrollment.objects.get(
            id=validated_data.pop("student_enrollment_id")
        )
        return Scholarship.objects.create(**validated_data)
