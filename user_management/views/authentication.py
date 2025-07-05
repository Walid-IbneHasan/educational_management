import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from institution.models import InstitutionInfo
from user_management.models.authentication import (
    User,
    InstitutionMembership,
    Invitation,
    ParentChildRelationship,
)
from user_management.serializers.authentication import (
    CustomTokenObtainPairSerializer,
    StudentIDSerializer,
    UserSerializer,
    RegisterSerializer,
    InstitutionSerializer,
    InstitutionMembershipSerializer,
    InvitationSerializer,
    AcceptInvitationSerializer,
    ParentChildRelationshipSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    UserCheckSerializer,
    VerifyOTPSerializer,
)
from user_management.services.authentication import AuthenticationService
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("user_management")

print("Loaded CustomTokenObtainPairView")


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        logger.debug(f"CustomTokenObtainPairView called with data: {request.data}")
        logger.debug(f"Using serializer: {self.serializer_class.__name__}")
        serializer = self.get_serializer(data=request.data)
        logger.debug(f"Serializer initialized: {serializer}")
        try:
            serializer.is_valid(raise_exception=True)
            logger.debug(f"Validated data: {serializer.validated_data}")
            return Response(serializer.validated_data, status=200)
        except Exception as e:
            logger.error(f"Serializer validation failed: {str(e)}")
            raise


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify OTP for registration",
        operation_description="""
        Verifies the OTP sent to the user's email or phone number during registration to activate their account.
        Returns JWT tokens upon successful verification.
        """,
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(
                description="Account activated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_STRING),
                        "tokens": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                                "access": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid OTP or identifier",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user, tokens = AuthenticationService.verify_otp(
                    identifier=serializer.validated_data["identifier"],
                    otp=serializer.validated_data["otp"],
                )
                return Response(
                    {"success": "Account activated successfully.", "tokens": tokens},
                    status=status.HTTP_200_OK,
                )
            except ValidationError as e:
                logger.error(f"OTP verification error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected OTP verification error: {str(e)}")
                return Response(
                    {"error": "Failed to verify OTP"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["register", "forget_password", "reset_password", "check"]:
            return [AllowAny()]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="""
        Registers a new user with a specified role (`institution` or `user`) using either an email or phone number.
        Institution users can create and manage institutions, while users with the `user` role are neutral until assigned
        a specific role (e.g., teacher, student) via an invitation. Upon successful registration:
        - For `role: "institution"`, sets `is_institution=true`, `is_admission_seeker=false`.
        - For `role: "user"`, sets `is_admission_seeker=true`, other flags `false`.
        - The password is hashed before storage.
        - Sends a 6-digit OTP via email or SMS for verification, and the user remains inactive until verified.
        - Returns the created user’s details and the OTP. Tokens are generated after OTP verification.
        """,
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_UUID,
                                    description="Unique identifier for the user",
                                ),
                                "email": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_EMAIL,
                                    nullable=True,
                                    description="The user’s unique email address",
                                ),
                                "phone_number": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="The user’s unique phone number",
                                ),
                                "first_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="The user’s first name",
                                ),
                                "last_name": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="The user’s last name",
                                ),
                                "gender": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    nullable=True,
                                    description="The user’s gender (male, female, other)",
                                ),
                                "birth_date": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_DATE,
                                    nullable=True,
                                    description="The user’s date of birth",
                                ),
                                "profile_image": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_URI,
                                    nullable=True,
                                    description="The user’s profile image",
                                ),
                                "is_institution": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Indicates if the user is an institution admin",
                                ),
                                "is_teacher": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Indicates if the user is a teacher",
                                ),
                                "is_student": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Indicates if the user is a student",
                                ),
                                "is_parents": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Indicates if the user is a parent",
                                ),
                                "is_admission_seeker": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN,
                                    description="Indicates if the user can join institutions",
                                ),
                            },
                            description="User details",
                        ),
                        "otp": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="6-digit OTP sent to email/phone",
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user, otp = AuthenticationService.register_user(
                    email=serializer.validated_data.get("email"),
                    phone_number=serializer.validated_data.get("phone_number"),
                    password=serializer.validated_data["password"],
                    role=serializer.validated_data["role"],
                )
                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "otp": otp,
                        "message": "OTP sent to your email or phone number. Verify to activate your account.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as e:
                logger.error(f"Registration error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected registration error: {str(e)}")
                return Response(
                    {"error": "Failed to register user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Check if user exists",
        operation_description="""
        Checks if a user exists by email or phone number. Returns whether the user exists and their active status.
        Used by the frontend to determine if the user should log in or register.
        """,
        request_body=UserCheckSerializer,
        responses={
            200: openapi.Response(
                description="User check result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "exists": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "is_active": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, nullable=True
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="check")
    def check(self, request):
        serializer = UserCheckSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = AuthenticationService.check_user(
                    email=serializer.validated_data.get("email"),
                    phone_number=serializer.validated_data.get("phone_number"),
                )
                return Response(result, status=status.HTTP_200_OK)
            except ValidationError as e:
                logger.error(f"User check error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected user check error: {str(e)}")
                return Response(
                    {"error": "Failed to check user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(
    #     operation_summary="Create or update user profile",
    #     operation_description="""
    # Allows an authenticated user to create (POST) or update (PATCH) their profile with fields: first_name, last_name,
    # gender, birth_date, and profile_image. The profile can only be created once; subsequent requests update the existing profile.
    # """,
    #     methods=["POST", "PATCH"],
    #     request_body=ProfileSerializer,
    #     responses={
    #         200: openapi.Response(
    #             description="Profile updated successfully", schema=UserSerializer()
    #         ),
    #         201: openapi.Response(
    #             description="Profile created successfully", schema=UserSerializer()
    #         ),
    #         400: openapi.Response(
    #             description="Invalid input or profile already created",
    #             schema=openapi.Schema(
    #                 type=openapi.TYPE_OBJECT,
    #                 properties={
    #                     "error": openapi.Schema(type=openapi.TYPE_STRING),
    #                 },
    #             ),
    #         ),
    #         401: openapi.Response(
    #             description="Unauthorized",
    #             schema=openapi.Schema(
    #                 type=openapi.TYPE_OBJECT,
    #                 properties={
    #                     "detail": openapi.Schema(type=openapi.TYPE_STRING),
    #                 },
    #             ),
    #         ),
    #     },
    # )
    @action(detail=False, methods=["get", "post", "patch"], url_path="profile")
    def profile(self, request):
        user = request.user
        if request.method == "GET":
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

        is_update = request.method == "PATCH"
        serializer = ProfileSerializer(data=request.data, partial=is_update)

        if serializer.is_valid():
            if not is_update and (user.first_name or user.last_name):
                return Response(
                    {"error": "Profile already created. Use PATCH to update."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            for attr, value in serializer.validated_data.items():
                setattr(user, attr, value)
            user.save()
            status_code = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED
            return Response(UserSerializer(user).data, status=status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Initiate password reset",
        operation_description="""
        Sends a 6-digit OTP to the user's email or phone number to initiate a password reset.
        Returns the OTP in the response for testing purposes, along with a success message.
        The OTP is valid for 10 minutes and can be used to reset the password via the `/auth/reset-password/` endpoint.
        """,
        request_body=ForgetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "otp": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="6-digit OTP sent to email/phone",
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid identifier",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="forget-password")
    def forget_password(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                identifier = serializer.validated_data.get(
                    "email"
                ) or serializer.validated_data.get("phone_number")
                otp = AuthenticationService.generate_and_send_otp(identifier)
                return Response(
                    {
                        "message": f"OTP sent to your { 'phone number' if serializer.validated_data.get('phone_number') else 'email' }",
                        "otp": otp,
                    },
                    status=status.HTTP_200_OK,
                )
            except ValidationError as e:
                logger.error(f"Forget password error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected forget password error: {str(e)}")
                return Response(
                    {"error": "Failed to initiate password reset"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Reset password using OTP",
        operation_description="""
        Resets the user's password after verifying the 6-digit OTP sent to their email or phone number.
        The OTP must be valid and unexpired (10-minute validity).
        """,
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid OTP or identifier",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="reset-password")
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                identifier = serializer.validated_data.get(
                    "email"
                ) or serializer.validated_data.get("phone_number")
                user = AuthenticationService.verify_otp_and_reset_password(
                    identifier=identifier,
                    otp=serializer.validated_data["otp"],
                    new_password=serializer.validated_data["new_password"],
                )
                return Response(
                    {"message": "Password reset successfully"},
                    status=status.HTTP_200_OK,
                )
            except ValidationError as e:
                logger.error(f"Reset password error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected reset password error: {str(e)}")
                return Response(
                    {"error": "Failed to reset password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Change authenticated user's password",
        operation_description="""
        Changes the authenticated user's password after verifying the current password. Requires JWT authentication.
        """,
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid current password",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            try:
                user = AuthenticationService.change_password(
                    user=request.user,
                    old_password=serializer.validated_data["old_password"],
                    new_password=serializer.validated_data["new_password"],
                )
                return Response(
                    {"message": "Password changed successfully"},
                    status=status.HTTP_200_OK,
                )
            except ValidationError as e:
                logger.error(f"Change password error: {str(e)}")
                error_message = (
                    e.message_dict["error"][0]
                    if hasattr(e, "message_dict") and e.message_dict
                    else str(e)
                )
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Unexpected change password error: {str(e)}")
                return Response(
                    {"error": "Failed to change password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        error_message = (
            next(iter(serializer.errors.values()))[0]
            if serializer.errors
            else "Invalid input"
        )
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="students/me")
    def get_student_id(self, request):
        user = request.user
        if not user.is_student:
            return Response(
                {"error": "User is not a student"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = StudentIDSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# user_management/views/authentication.py


class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = InstitutionInfo.objects.select_related("admin")
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 15))
    @swagger_auto_schema(
        operation_summary="List all institutions",
        operation_description="Retrieves a list of all institutions in the system. Cached for 15 minutes.",
        responses={
            200: InstitutionSerializer(many=True),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new institution",
        operation_description="""
        Creates a new educational institution for an authenticated user with `is_institution=true`.
        The user becomes the admin of the institution. Includes optional fields for institution type, address, and short code.
        """,
        request_body=InstitutionSerializer,
        responses={
            201: openapi.Response(
                description="Institution created successfully",
                schema=InstitutionSerializer(),
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def perform_create(self, serializer):
        try:
            institution = AuthenticationService.create_institution(
                self.request.user,
                serializer.validated_data["name"],
                serializer.validated_data.get("institution_type"),
                serializer.validated_data.get("address"),
                serializer.validated_data.get("short_code"),
            )
            serializer.instance = institution
        except Exception as e:
            logger.error(f"Institution creation error: {str(e)}")
            raise


class InstitutionMembershipViewSet(viewsets.ModelViewSet):
    queryset = InstitutionMembership.objects.select_related("user", "institution")
    serializer_class = InstitutionMembershipSerializer
    permission_classes = [IsAuthenticated]


class UserInstitutionsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        institutions = InstitutionInfo.objects.filter(memberships__user=user).distinct()
        serializer = InstitutionSerializer(institutions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.select_related("institution")
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "accept":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Invitation.objects.none()
        user = self.request.user
        logger.debug(
            f"User: {user}, is_authenticated: {user.is_authenticated}, email: {user.email}, phone_number: {user.phone_number}"
        )

        if not user.is_authenticated:
            logger.warning("Unauthenticated user attempted to access invitations")
            return Invitation.objects.none()

        if user.is_institution:
            # Institution admins see only invitations from their institution
            institution = user.institution_info.first()
            if institution:
                logger.debug(
                    f"Institution admin accessing invitations for institution: {institution.id}"
                )
                return self.queryset.filter(institution=institution)
            logger.warning(f"No institution found for admin user: {user.id}")
            return Invitation.objects.none()
        else:
            # Non-institution users (including those with no role) see invitations sent to their email or phone number
            if not user.email and not user.phone_number:
                logger.warning(f"User {user.id} has neither email nor phone_number set")
                return Invitation.objects.none()

            query = models.Q()
            if user.email:
                query |= models.Q(email=user.email)
            if user.phone_number:
                query |= models.Q(phone_number=user.phone_number)

            logger.debug(
                f"Filtering invitations for user {user.id} with query: {query}"
            )
            return self.queryset.filter(query)

    @swagger_auto_schema(
        operation_summary="Create an invitation",
        operation_description="""
    Creates an invitation for a user to join an institution as a teacher or student.
    Sends an email or SMS with a unique token based on whether an email or phone number is provided.
    """,
        request_body=InvitationSerializer,
        responses={
            201: openapi.Response(
                description="Invitation created successfully",
                schema=InvitationSerializer(),
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def perform_create(self, serializer):
        try:
            invitation = AuthenticationService.create_invitation(
                email=serializer.validated_data.get("email"),
                phone_number=serializer.validated_data.get("phone_number"),
                role=serializer.validated_data["role"],
                admin=self.request.user,
            )
            serializer.instance = invitation
        except Exception as e:
            logger.error(f"Invitation creation error: {str(e)}")
            raise

    @swagger_auto_schema(
        method="post",
        operation_summary="Accept an invitation (API)",
        operation_description="""
    Accepts an invitation via API by validating the token and assigning the user to an institution
    with the specified role (teacher or student). Requires the user to be authenticated and have
    an email or phone number matching the invitation.
    """,
        request_body=AcceptInvitationSerializer,
        responses={
            200: openapi.Response(
                description="Invitation accepted successfully",
                schema=InvitationSerializer(),
            ),
            400: openapi.Response(
                description="Invalid token or identifier mismatch",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @swagger_auto_schema(
        method="get",
        operation_summary="Accept an invitation (Web)",
        operation_description="""
        Handles web-based invitation acceptance by redirecting to a login page or an acceptance page
        based on the user's authentication status. The token is passed as a query parameter.
        """,
        manual_parameters=[
            openapi.Parameter(
                "token",
                openapi.IN_QUERY,
                description="The unique token from the invitation link",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
            ),
        ],
        responses={
            302: openapi.Response(
                description="Redirect to login or acceptance page",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "location": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post", "get"], url_path="accept")
    def accept(self, request):
        if request.method == "GET":
            token = request.query_params.get("token")
            if not token:
                logger.error("No token provided in GET request")
                return Response(
                    {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            return redirect(f"{reverse('invitation-accept-web')}?token={token}")

        serializer = AcceptInvitationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                invitation = AuthenticationService.accept_invitation(
                    self.request.user, serializer.validated_data["token"]
                )
                return Response(
                    InvitationSerializer(invitation).data, status=status.HTTP_200_OK
                )
            except ValidationError as e:
                logger.error(f"Invitation acceptance error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected invitation acceptance error: {str(e)}")
                return Response(
                    {"error": "Failed to accept invitation"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response({"error": "Invalid input"}, status=status.HTTP_400_BAD_REQUEST)


class ParentChildRelationshipViewSet(viewsets.ModelViewSet):
    queryset = ParentChildRelationship.objects.select_related("parent", "child")
    serializer_class = ParentChildRelationshipSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a parent-child relationship",
        operation_description="""
    Links an authenticated user (intended parent) to a student user, allowing the parent to monitor
    the student’s progress. Validates that the child is a student.
    """,
        request_body=ParentChildRelationshipSerializer,
        responses={
            201: openapi.Response(
                description="Parent-child relationship created successfully",
                schema=ParentChildRelationshipSerializer(),
            ),
            400: openapi.Response(
                description="Invalid child ID or child is not a student",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def perform_create(self, serializer):
        try:
            relationship = AuthenticationService.create_parent_child_relationship(
                parent=self.request.user,
                child_id=serializer.validated_data["child_id"],
            )
            serializer.instance = relationship
        except Exception as e:
            logger.error(f"Parent-child relationship creation error: {str(e)}")
            raise


class StudentTeacherViewset(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        models.Q(is_student=True) | models.Q(is_teacher=True)
    )
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="members")
    def members(self, request):
        user = request.user
        if not user.is_institution:
            logger.error(
                f"Non-institution user attempted to access members: user_id={user.id}"
            )
            return Response(
                {"error": "Only institution admins can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )
        institution = user.institution_info.first()
        if not institution:
            logger.error(f"No institution found for admin: user_id={user.id}")
            return Response(
                {"error": "No institution found for this admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        memberships = InstitutionMembership.objects.filter(
            institution=institution, role__in=["student", "teacher"]
        ).select_related("user")

        data = [
            {
                "user": UserSerializer(membership.user).data,
                "role": membership.role,
            }
            for membership in memberships
        ]

        logger.info(
            f"Retrieved {len(data)} members for institution: institution_id={institution.id}"
        )
        return Response(data, status=status.HTTP_200_OK)
