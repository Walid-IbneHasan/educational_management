from rest_framework import serializers
from institution.models import InstitutionInfo
from user_management.models.admission_seeker import AdmissionRequest
from user_management.models.authentication import  Invitation
from django.core.exceptions import ValidationError

from user_management.serializers.authentication import UserSerializer


class AdmissionRequestSerializer(serializers.ModelSerializer):
    institution_id = serializers.UUIDField(write_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    user = UserSerializer(read_only=True)
    institution = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AdmissionRequest
        fields = [
            "id",
            "user",
            "institution",
            "institution_id",
            "institution_name",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "institution",
            "institution_name",
            "status",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the admission request."},
            "user": {"help_text": "The ID of the user requesting admission."},
            "institution": {"help_text": "The name of the institution."},
            "institution_id": {
                "help_text": "The ID of the institution to request admission to."
            },
            "institution_name": {"help_text": "The name of the institution."},
            "status": {
                "help_text": "The status of the request (pending, approved, rejected)."
            },
            "created_at": {"help_text": "The date and time the request was created."},
            "updated_at": {
                "help_text": "The date and time the request was last updated."
            },
        }

    def validate_institution_id(self, value):
        institution = InstitutionInfo.objects.filter(id=value).first()
        if not institution:
            raise serializers.ValidationError("Institution not found.")
        return value

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_admission_seeker:
            raise serializers.ValidationError("User is not an admission seeker.")
        institution_id = data["institution_id"]
        if AdmissionRequest.objects.filter(
            user=user, institution_id=institution_id, status="pending"
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending admission request for this institution."
            )
        return data




class AdmissionActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])

    def validate_action(self, value):
        return value


class InstitutionRequestSerializer(serializers.ModelSerializer):
    institution = serializers.StringRelatedField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "institution",
            "role",
            "status",
            "token",
            "created_at",
            "expires_at",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the invitation."},
            "institution": {"help_text": "The name of the institution."},
            "role": {"help_text": "The role offered (teacher, student)."},
            "status": {
                "help_text": "The status of the invitation (pending, accepted, expired)."
            },
            "token": {"help_text": "The unique token for the invitation."},
            "created_at": {
                "help_text": "The date and time the invitation was created."
            },
            "expires_at": {"help_text": "The date and time the invitation expires."},
        }

    def get_status(self, obj):
        from django.utils import timezone

        if obj.is_used:
            return "accepted"
        if obj.expires_at < timezone.now():
            return "expired"
        return "pending"
