from rest_framework import serializers
from user_management.models.authentication import User


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "is_teacher",
            "is_student",
            "is_institution",
            "is_parents",
            "is_admission_seeker",
        ]
        extra_kwargs = {
            "is_teacher": {"help_text": "Indicates if the user is a teacher."},
            "is_student": {"help_text": "Indicates if the user is a student."},
            "is_institution": {
                "help_text": "Indicates if the user is an institution admin."
            },
            "is_parents": {"help_text": "Indicates if the user is a parent."},
            "is_admission_seeker": {
                "help_text": "Indicates if the user can join institutions."
            },
        }
