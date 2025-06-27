from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from user_management.models.authentication import (
    User,
    Institution,
    InstitutionMembership,
    Invitation,
    ParentChildRelationship,
)
import uuid
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.core import mail
from django.test.utils import override_settings
import fakeredis
import logging
from unittest.mock import patch

logger = logging.getLogger(__name__)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DJANGO_TEST="True"
)
class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.register_url = reverse("authentication:user-register")
        self.login_url = reverse("authentication:token-obtain-pair")
        self.users_url = reverse("authentication:user-list")
        self.institutions_url = reverse("authentication:institution-list")
        self.institution_detail_url = lambda pk: reverse(
            "authentication:institution-detail", kwargs={"pk": pk}
        )
        self.memberships_url = reverse("authentication:membership-list")
        self.invitations_url = reverse("authentication:invitation-list")
        self.invitation_accept_url = reverse("authentication:invitation-accept")
        self.parent_child_url = reverse("authentication:parent-child-list")
        self.token_refresh_url = reverse("authentication:token-refresh")
        self.forget_password_url = reverse("authentication:forget-password")
        self.reset_password_url = reverse("authentication:reset-password")
        self.change_password_url = reverse("authentication:change-password")

        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
            is_institution=True,
            is_admission_seeker=False,
        )
        self.teacher_user = User.objects.create_user(
            email="teacher@example.com",
            password="securepassword123",
            first_name="Jane",
            last_name="Smith",
            is_admission_seeker=True,
            is_student=False,
        )
        self.student_user = User.objects.create_user(
            email="student@example.com",
            password="securepassword123",
            first_name="Student",
            last_name="User",
            is_admission_seeker=True,
            is_student=True,
        )
        self.parent_user = User.objects.create_user(
            email="parent@example.com",
            password="securepassword123",
            first_name="Alice",
            last_name="Brown",
            is_admission_seeker=True,
        )

        # Create an institution
        self.institution = Institution.objects.create(
            name="Example University", admin=self.admin_user
        )

        # Patch redis_client in services.authentication
        self.patcher = patch(
            "user_management.services.authentication.redis_client", self.redis_client
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    def test_register_institution_user_success(self):
        """Test successful registration of an institution user"""
        data = {
            "email": "newadmin@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "Admin",
            "role": "institution",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "newadmin@example.com")
        self.assertTrue(response.data["is_institution"])
        self.assertFalse(response.data["is_admission_seeker"])
        user = User.objects.get(email="newadmin@example.com")
        self.assertTrue(user.check_password("securepassword123"))

    def test_register_user_success(self):
        """Test successful registration of a neutral user"""
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
            "role": "user",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "newuser@example.com")
        self.assertFalse(response.data["is_institution"])
        self.assertTrue(response.data["is_admission_seeker"])
        self.assertFalse(response.data["is_student"])
        self.assertFalse(response.data["is_teacher"])

    def test_register_existing_email(self):
        """Test registration with an existing email"""
        data = {
            "email": "admin@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "institution",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            str(response.data["email"][0]), "user with this email already exists."
        )

    def test_register_invalid_role(self):
        """Test registration with an invalid role"""
        data = {
            "email": "invalid@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "invalid",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)
        self.assertEqual(
            str(response.data["role"][0]), '"invalid" is not a valid choice.'
        )

    def test_login_success(self):
        """Test successful login with valid credentials"""
        data = {"email": "admin@example.com", "password": "securepassword123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        """Test login with incorrect password"""
        data = {"email": "admin@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            str(response.data["detail"]),
            "No active account found with the given credentials",
        )

    def test_login_nonexistent_email(self):
        """Test login with non-existent email"""
        data = {"email": "nonexistent@example.com", "password": "securepassword123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            str(response.data["detail"]),
            "No active account found with the given credentials",
        )

    def test_list_users_authenticated(self):
        """Test listing users as an authenticated user"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(self.users_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_users_unauthenticated(self):
        """Test listing users without authentication"""
        response = self.client.get(self.users_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            str(response.data["detail"]),
            "Authentication credentials were not provided.",
        )

    def test_create_institution_success(self):
        """Test creating an institution as an institution user"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"name": "New University"}
        response = self.client.post(self.institutions_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New University")
        self.assertEqual(str(response.data["admin"]), str(self.admin_user.id))
        institution = Institution.objects.get(name="New University")
        self.assertEqual(institution.admin, self.admin_user)

    def test_create_institution_non_institution_user(self):
        """Test creating an institution as a non-institution user"""
        tokens = self.get_tokens_for_user(self.teacher_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"name": "New University"}
        response = self.client.post(self.institutions_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data["detail"]),
            "You do not have permission to perform this action.",
        )

    def test_list_institutions_authenticated(self):
        """Test listing institutions as an authenticated user"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(self.institutions_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]["name"], "Example University")

    def test_retrieve_institution_success(self):
        """Test retrieving an institution by ID"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(
            self.institution_detail_url(self.institution.id), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Example University")
        self.assertEqual(str(response.data["admin"]), str(self.admin_user.id))

    def test_list_memberships_authenticated(self):
        """Test listing memberships as a member"""
        membership = InstitutionMembership.objects.create(
            user=self.teacher_user, institution=self.institution, role="teacher"
        )
        tokens = self.get_tokens_for_user(self.teacher_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(self.memberships_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(str(response.data[0]["user"]), str(self.teacher_user.id))
        self.assertEqual(response.data[0]["role"], "teacher")

    def test_list_memberships_no_membership(self):
        """Test listing memberships without being a member"""
        tokens = self.get_tokens_for_user(self.parent_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(self.memberships_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data["detail"]),
            "You do not have permission to perform this action.",
        )

    def test_create_invitation_success(self):
        """Test creating an invitation as an institution admin"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            tokens = self.get_tokens_for_user(self.admin_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"email": "newteacher@example.com", "role": "teacher"}
            response = self.client.post(self.invitations_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["email"], "newteacher@example.com")
            self.assertEqual(response.data["role"], "teacher")
            self.assertEqual(
                str(response.data["institution"]), str(self.institution.id)
            )
            self.assertFalse(response.data["is_used"])
            self.assertIn("invitation_link", response.data)
            self.assertIn("token", response.data)
            # Verify email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Tutoria Invitation")
            self.assertIn(
                "http://localhost:8000/auth/invitations/accept/?token=",
                mail.outbox[0].alternatives[0][0],
            )

    def test_create_invitation_non_admin(self):
        """Test creating an invitation as a non-admin"""
        tokens = self.get_tokens_for_user(self.teacher_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"email": "newteacher@example.com", "role": "teacher"}
        response = self.client.post(self.invitations_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data["detail"]),
            "You do not have permission to perform this action.",
        )

    def test_create_invitation_invalid_role(self):
        """Test creating an invitation with an invalid role"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"email": "newteacher@example.com", "role": "invalid"}
        response = self.client.post(self.invitations_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)
        self.assertEqual(
            str(response.data["role"][0]), '"invalid" is not a valid choice.'
        )

    def test_accept_invitation_success(self):
        """Test accepting an invitation as a registered user"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            invitation = Invitation.objects.create(
                email="teacher@example.com",
                institution=self.institution,
                role="teacher",
                token=uuid.uuid4(),
                created_at=timezone.now(),
                expires_at=timezone.now() + timedelta(days=7),
            )
            # Set Redis key as AuthenticationService would
            self.redis_client.setex(
                f"invitation:{invitation.token}", 604800, str(invitation.id)
            )
            # Debug Redis key
            redis_value = self.redis_client.get(f"invitation:{invitation.token}")
            logger.debug(f"Redis key invitation:{invitation.token} = {redis_value}")
            tokens = self.get_tokens_for_user(self.teacher_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"token": str(invitation.token)}
            response = self.client.post(self.invitation_accept_url, data, format="json")
            logger.debug(f"Response data: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data["is_used"])
            self.assertEqual(response.data["email"], "teacher@example.com")
            self.assertEqual(response.data["role"], "teacher")
            # Verify membership
            membership = InstitutionMembership.objects.get(
                user=self.teacher_user, institution=self.institution
            )
            self.assertEqual(membership.role, "teacher")
            # Verify user role
            self.teacher_user.refresh_from_db()
            self.assertTrue(self.teacher_user.is_teacher)
            # Verify Redis key is deleted
            self.assertIsNone(self.redis_client.get(f"invitation:{invitation.token}"))

    def test_accept_invitation_invalid_token(self):
        """Test accepting an invitation with an invalid token"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            tokens = self.get_tokens_for_user(self.teacher_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"token": str(uuid.uuid4())}
            response = self.client.post(self.invitation_accept_url, data, format="json")
            logger.debug(f"Response data: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                str(response.data["error"]), "Invalid or expired invitation token"
            )

    def test_accept_invitation_email_mismatch(self):
        """Test accepting an invitation with a mismatched email"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            invitation = Invitation.objects.create(
                email="wrong@example.com",
                institution=self.institution,
                role="teacher",
                token=uuid.uuid4(),
                created_at=timezone.now(),
                expires_at=timezone.now() + timedelta(days=7),
            )
            self.redis_client.setex(
                f"invitation:{invitation.token}", 604800, str(invitation.id)
            )
            tokens = self.get_tokens_for_user(self.teacher_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"token": str(invitation.token)}
            response = self.client.post(self.invitation_accept_url, data, format="json")
            logger.debug(f"Response data: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                str(response.data["error"]),
                "Invitation email does not match user email",
            )

    def test_accept_invitation_expired(self):
        """Test accepting an expired invitation"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            invitation = Invitation.objects.create(
                email="teacher@example.com",
                institution=self.institution,
                role="teacher",
                token=uuid.uuid4(),
                created_at=timezone.now() - timedelta(days=8),
                expires_at=timezone.now() - timedelta(days=1),
            )
            self.redis_client.setex(
                f"invitation:{invitation.token}", 604800, str(invitation.id)
            )
            tokens = self.get_tokens_for_user(self.teacher_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"token": str(invitation.token)}
            response = self.client.post(self.invitation_accept_url, data, format="json")
            logger.debug(f"Response data: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(str(response.data["error"]), "Invitation has expired")

    def test_accept_invitation_already_used(self):
        """Test accepting an already used invitation"""
        with patch(
            "user_management.services.authentication.redis_client", self.redis_client
        ):
            invitation = Invitation.objects.create(
                email="teacher@example.com",
                institution=self.institution,
                role="teacher",
                token=uuid.uuid4(),
                created_at=timezone.now(),
                expires_at=timezone.now() + timedelta(days=7),
                is_used=True,
            )
            self.redis_client.setex(
                f"invitation:{invitation.token}", 604800, str(invitation.id)
            )
            tokens = self.get_tokens_for_user(self.teacher_user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
            data = {"token": str(invitation.token)}
            response = self.client.post(self.invitation_accept_url, data, format="json")
            logger.debug(f"Response data: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(str(response.data["error"]), "Invitation already used")

    def test_create_parent_child_success(self):
        """Test creating a parent-child relationship"""
        tokens = self.get_tokens_for_user(self.parent_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"child_id": str(self.student_user.id)}
        response = self.client.post(self.parent_child_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["parent"]), str(self.parent_user.id))
        self.assertEqual(str(response.data["child"]), str(self.student_user.id))
        self.parent_user.refresh_from_db()
        self.assertTrue(self.parent_user.is_parents)

    def test_list_parent_child_authenticated(self):
        """Test listing parent-child relationships"""
        ParentChildRelationship.objects.create(
            parent=self.parent_user, child=self.student_user
        )
        tokens = self.get_tokens_for_user(self.parent_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get(self.parent_child_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(str(response.data[0]["parent"]), str(self.parent_user.id))
        self.assertEqual(str(response.data[0]["child"]), str(self.student_user.id))

    def test_token_refresh_success(self):
        """Test refreshing a JWT token"""
        tokens = self.get_tokens_for_user(self.admin_user)
        data = {"refresh": tokens["refresh"]}
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid(self):
        """Test refreshing with an invalid token"""
        data = {"refresh": "invalid-token"}
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data["detail"]), "Token is invalid")

    def test_forget_password_success(self):
        """Test successful initiation of password reset with OTP"""
        data = {"email": self.admin_user.email}
        response = self.client.post(self.forget_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent to your email")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Tutoria Password Reset OTP", mail.outbox[0].subject)
        self.assertIn(
            "Your OTP for password reset is:", mail.outbox[0].alternatives[0][0]
        )
        otp = self.redis_client.get(f"otp:{self.admin_user.email}")
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 6)

    def test_forget_password_invalid_email(self):
        """Test password reset initiation with non-existent email"""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.forget_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["error"]), "No user with this email exists.")
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_success(self):
        """Test successful password reset with valid OTP"""
        # Generate OTP
        self.client.post(self.forget_password_url, {"email": self.admin_user.email})
        otp = self.redis_client.get(f"otp:{self.admin_user.email}")
        data = {
            "email": self.admin_user.email,
            "otp": otp,
            "new_password": "newsecurepassword123",
        }
        response = self.client.post(self.reset_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset successfully")
        user = User.objects.get(email=self.admin_user.email)
        self.assertTrue(user.check_password("newsecurepassword123"))
        self.assertIsNone(self.redis_client.get(f"otp:{self.admin_user.email}"))

    def test_reset_password_invalid_otp(self):
        """Test password reset with invalid OTP"""
        self.client.post(self.forget_password_url, {"email": self.admin_user.email})
        data = {
            "email": self.admin_user.email,
            "otp": "123456",
            "new_password": "newsecurepassword123",
        }
        response = self.client.post(self.reset_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["error"]), "Invalid or expired OTP")

    def test_change_password_success(self):
        """Test successful password change for authenticated user"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {
            "old_password": "securepassword123",
            "new_password": "newsecurepassword123",
        }
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password changed successfully")
        user = User.objects.get(email=self.admin_user.email)
        self.assertTrue(user.check_password("newsecurepassword123"))

    def test_change_password_invalid_old_password(self):
        """Test password change with incorrect old password"""
        tokens = self.get_tokens_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        data = {"old_password": "wrongpassword", "new_password": "newsecurepassword123"}
        response = self.client.post(self.change_password_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["error"]), "Current password is incorrect.")
