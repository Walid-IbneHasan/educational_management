from rest_framework import serializers
from notice.models import Notice
from user_management.serializers.authentication import UserSerializer


class NoticeSerializer(serializers.ModelSerializer):


    class Meta:
        model = Notice
        fields = [
            "id",
            "institution",
            "title",
            "content",
            "target_audience",
            "notice_type",
            "image",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "institution",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        request = self.context["request"]
        # Ensure the user is an admin of an institution
        if not request.user.is_institution:
            raise serializers.ValidationError(
                {"non_field_errors": "Only institution admins can create notices."}
            )
        institution = request.user.institution_info.first()
        if not institution:
            raise serializers.ValidationError(
                {"non_field_errors": "No institution found for this admin."}
            )
        return data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["institution"] = self.context[
            "request"
        ].user.institution_info.first()
        return super().create(validated_data)
