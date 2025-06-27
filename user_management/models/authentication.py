import uuid
from datetime import timedelta
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

from institution.models import InstitutionInfo


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not (email or phone_number):
            raise ValueError("Either email or phone number must be set")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^(0\d{10}|88\d{10}|880\d{10})$",
                message="Phone number must be 11 digits starting with '0' (e.g., 01746134904), or 12 digits starting with '88', or 13 digits starting with '880'.",
            )
        ],
    )
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        null=True,
        blank=True,
    )
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )
    is_institution = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_parents = models.BooleanField(default=False)
    is_admission_seeker = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return self.email or self.phone_number or f"User {self.id}"


class InstitutionMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=[("teacher", "Teacher"), ("student", "Student")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "institution")
        indexes = [
            models.Index(fields=["user", "institution"]),
        ]


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^(0\d{10}|88\d{10}|880\d{10})$",
                message="Phone number must be 11 digits starting with '0' (e.g., 01746134904), or 12 digits starting with '88', or 13 digits starting with '880'.",
            )
        ],
    )
    institution = models.ForeignKey(
        InstitutionInfo, on_delete=models.CASCADE, related_name="invitations"
    )
    role = models.CharField(
        max_length=20, choices=[("teacher", "Teacher"), ("student", "Student")]
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(days=7))
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["token"]),
        ]

    def save(self, *args, **kwargs):
        if not (self.email or self.phone_number):
            raise ValueError("Either email or phone number must be provided")
        super().save(*args, **kwargs)


class ParentChildRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children")
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("parent", "child")
        indexes = [
            models.Index(fields=["parent", "child"]),
        ]
