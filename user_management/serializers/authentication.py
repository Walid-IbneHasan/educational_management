from rest_framework import serializers
from institution.models import InstitutionInfo
from user_management.models.authentication import (
    User,
    InstitutionMembership,
    Invitation,
    ParentChildRelationship,
)
from django.core.validators import RegexValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import re

import logging


logger = logging.getLogger("user_management")


def validate_password_strength(password):
    if len(password) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )
    if not re.search(r"[A-Z]", password):
        raise serializers.ValidationError(
            "Password must contain at least one uppercase letter."
        )
    if not re.search(r"[a-z]", password):
        raise serializers.ValidationError(
            "Password must contain at least one lowercase letter."
        )
    if not re.search(r"\d", password):
        raise serializers.ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()_+]", password):
        raise serializers.ValidationError(
            "Password must contain at least one special character."
        )
    return password


class ValidatedPhoneNumberField(serializers.CharField):
    def to_internal_value(self, data):
        logger.debug(f"ValidatedPhoneNumberField to_internal_value: {data}")
        phone_number = str(data).strip().replace(" ", "")
        if phone_number.startswith("+880"):
            phone_number = "0" + phone_number[4:]
        elif not phone_number.startswith("0"):
            raise serializers.ValidationError(
                "Phone number must start with '0' or '+880'."
            )
        if not re.match(r"^0\d{10}$", phone_number):
            raise serializers.ValidationError(
                "Phone number must be 11 digits starting with '0'."
            )
        return phone_number

    def to_representation(self, value):
        logger.debug(f"ValidatedPhoneNumberField to_representation: {value}")
        if value:
            phone_number = str(value).strip().replace(" ", "")
            if phone_number.startswith("+880"):
                phone_number = "0" + phone_number[4:]
            elif phone_number.startswith("880"):
                phone_number = "0" + phone_number[3:]
            elif not phone_number.startswith("0"):
                phone_number = "0" + phone_number
            return phone_number
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default username_field (e.g., email) to prevent required validation
        self.fields.pop(self.username_field, None)
        # Explicitly define fields
        self.fields["email"] = serializers.EmailField(required=False, allow_blank=True)
        self.fields["phone_number"] = ValidatedPhoneNumberField(
            required=False, allow_blank=True
        )
        self.fields["password"] = serializers.CharField(write_only=True)
        logger.debug(f"CustomTokenObtainPairSerializer fields: {self.fields}")

    def validate(self, attrs):
        logger.debug(f"CustomTokenObtainPairSerializer validate: {attrs}")
        if not (attrs.get("email") or attrs.get("phone_number")):
            logger.error(
                "Validation failed: Either email or phone number must be provided."
            )
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )

        user = None
        if attrs.get("email"):
            logger.debug(f"Looking up user by email: {attrs['email']}")
            user = User.objects.filter(email=attrs["email"]).first()
        elif attrs.get("phone_number"):
            logger.debug(f"Looking up user by phone_number: {attrs['phone_number']}")
            user = User.objects.filter(phone_number=attrs["phone_number"]).first()

        if not user:
            logger.error(f"No user found for credentials: {attrs}")
            raise serializers.ValidationError(
                "No user found with the provided credentials."
            )
        if not user.check_password(attrs["password"]):
            logger.error(
                f"Incorrect password for user: {user.phone_number or user.email}"
            )
            raise serializers.ValidationError("Incorrect password.")
        if not user.is_active:
            logger.error(f"Inactive account: {user.phone_number or user.email}")
            raise serializers.ValidationError(
                "User account is not active. Please verify your OTP."
            )

        # Generate tokens directly, bypassing super().validate
        data = {}
        refresh = RefreshToken.for_user(user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        logger.info(f"Login successful for user: {user.phone_number or user.email}")
        return data


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True, required=False)
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "profile_image",
            "role",
            "is_institution",
            "is_teacher",
            "is_student",
            "is_parents",
            "is_admission_seeker",
        ]
        read_only_fields = [
            "id",
            "is_institution",
            "is_teacher",
            "is_student",
            "is_parents",
            "is_admission_seeker",
        ]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the user."},
            "email": {"help_text": "The user’s unique email address."},
            "phone_number": {"help_text": "The user’s unique phone number."},
            "first_name": {"help_text": "The user’s first name."},
            "last_name": {"help_text": "The user’s last name."},
            "gender": {"help_text": "The user’s gender (male, female, other)."},
            "birth_date": {"help_text": "The user’s date of birth."},
            "profile_image": {"help_text": "The user’s profile image."},
            "role": {
                "help_text": "The user’s role during registration ('institution' or 'user')."
            },
            "is_institution": {
                "help_text": "Indicates if the user is an institution admin."
            },
            "is_teacher": {"help_text": "Indicates if the user is a teacher."},
            "is_student": {"help_text": "Indicates if the user is a student."},
            "is_parents": {"help_text": "Indicates if the user is a parent."},
            "is_admission_seeker": {
                "help_text": "Indicates if the user can join institutions."
            },
        }


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["institution", "user"])

    def validate(self, data):
        if not (data.get("email") or data.get("phone_number")):
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        if data.get("email"):
            user = User.objects.filter(email=data["email"]).first()
            if user and user.is_active:
                raise serializers.ValidationError({"email": "Email already exists."})
        if data.get("phone_number"):
            user = User.objects.filter(phone_number=data["phone_number"]).first()
            if user and user.is_active:
                raise serializers.ValidationError(
                    {"phone_number": "Phone number already exists."}
                )
        return data

    def validate_password(self, value):
        validate_password_strength(value)
        return value


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    otp = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_identifier(self, value):
        if "@" in value:
            if not serializers.EmailField().to_internal_value(value):
                raise serializers.ValidationError("Invalid email format.")
        else:
            value = ValidatedPhoneNumberField().to_internal_value(value)
        return value


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "gender", "birth_date", "profile_image"]
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "gender": {"required": True},
            "birth_date": {"required": True},
            "profile_image": {"required": False},
        }


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionInfo
        fields = [
            "id",
            "name",
            "institution_type",
            "address",
            "short_code",
            "admin",
            "created_at",
        ]
        read_only_fields = ["id", "admin", "created_at"]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the institution."},
            "name": {"help_text": "The name of the institution."},
            "institution_type": {
                "help_text": "The type of institution (e.g., university, school)."
            },
            "address": {"help_text": "The physical address of the institution."},
            "short_code": {"help_text": "A unique short code for the institution."},
            "admin": {
                "help_text": "The ID of the user who is the admin of the institution."
            },
            "created_at": {
                "help_text": "The date and time the institution was created."
            },
        }


class InstitutionMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionMembership
        fields = ["id", "user", "institution", "role", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the membership."},
            "user": {"help_text": "The ID of the user who is a member."},
            "institution": {"help_text": "The ID of the institution."},
            "role": {
                "help_text": "The role of the user in the institution (e.g., teacher, student)."
            },
            "created_at": {
                "help_text": "The date and time the membership was created."
            },
        }


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionInfo
        fields = ["id", "name"]


class InvitationSerializer(serializers.ModelSerializer):
    invitation_link = serializers.SerializerMethodField()
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "phone_number",
            "institution",
            "role",
            "token",
            "invitation_link",
            "created_at",
            "expires_at",
            "is_used",
        ]
        read_only_fields = [
            "id",
            "institution",
            "token",
            "invitation_link",
            "created_at",
            "expires_at",
            "is_used",
        ]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the invitation."},
            "email": {"help_text": "The email address of the invited user."},
            "phone_number": {"help_text": "The phone number of the invited user."},
            "institution": {
                "help_text": "The ID of the institution sending the invitation."
            },
            "role": {
                "help_text": "The role to assign to the invited user (e.g., teacher, student)."
            },
            "token": {"help_text": "The unique token for the invitation."},
            "invitation_link": {
                "help_text": "The link sent in the invitation email or SMS."
            },
            "created_at": {
                "help_text": "The date and time the invitation was created."
            },
            "expires_at": {"help_text": "The date and time the invitation expires."},
            "is_used": {"help_text": "Indicates if the invitation has been used."},
        }

    def validate(self, data):
        if not (data.get("email") or data.get("phone_number")):
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        return data

    def get_invitation_link(self, obj):
        return f"http://localhost:8000/auth/invitations/accept/?token={obj.token}"


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField(
        help_text="The unique token from the invitation link."
    )


class ParentChildRelationshipSerializer(serializers.ModelSerializer):
    child_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ParentChildRelationship
        fields = ["id", "parent", "child", "child_id", "created_at"]
        read_only_fields = ["id", "parent", "child", "created_at"]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the relationship."},
            "parent": {"help_text": "The ID of the parent user."},
            "child": {"help_text": "The ID of the student user."},
            "child_id": {"help_text": "The ID of the student user to link as a child."},
            "created_at": {
                "help_text": "The date and time the relationship was created."
            },
        }


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)

    def validate(self, data):
        if not (data.get("email") or data.get("phone_number")):
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        if data.get("email") and not User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "No user with this email exists."}
            )
        if (
            data.get("phone_number")
            and not User.objects.filter(phone_number=data["phone_number"]).exists()
        ):
            raise serializers.ValidationError(
                {"phone_number": "No user with this phone number exists."}
            )
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if not (data.get("email") or data.get("phone_number")):
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        return data

    def validate_new_password(self, value):
        validate_password_strength(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password_strength(value)
        return value

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "Current password is incorrect."}
            )
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from old password."}
            )
        return data


class UserCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)

    def validate(self, data):
        if not (data.get("email") or data.get("phone_number")):
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        return data


class StudentIDSerializer(serializers.ModelSerializer):
    phone_number = ValidatedPhoneNumberField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "email", "phone_number"]
        read_only_fields = ["id", "email", "phone_number"]
        extra_kwargs = {
            "id": {"help_text": "Unique identifier for the student."},
            "email": {"help_text": "The student’s email address."},
            "phone_number": {"help_text": "The student’s phone number."},
        }
