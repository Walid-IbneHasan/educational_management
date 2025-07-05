from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from institution.models import InstitutionInfo
from user_management.models.admission_seeker import AdmissionRequest
from user_management.models.authentication import Invitation, User
from user_management.serializers.admission_seeker import (
    AdmissionRequestSerializer,
    AdmissionActionSerializer,
    InstitutionRequestSerializer,
)
from user_management.serializers.authentication import UserSerializer
from user_management.services.admission_seeker import AdmissionService
from rest_framework.permissions import IsAuthenticated
import logging
from django.db import models
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class AdmissionRequestViewSet(viewsets.ModelViewSet):
    queryset = AdmissionRequest.objects.select_related("user", "institution")
    serializer_class = AdmissionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                AdmissionRequest.objects.none()
            )  # Return empty queryset for schema generation
        user = self.request.user
        if not user.is_authenticated:
            return AdmissionRequest.objects.none()
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return self.queryset.filter(institution=institution)
        return self.queryset.filter(user=user)

    @swagger_auto_schema(
        operation_summary="Create an admission request",
        operation_description="""
        Allows an admission seeker (is_admission_seeker=True) to send an admission request to an institution.
        The request is pending until approved or rejected by the institution admin.
        """,
        request_body=AdmissionRequestSerializer,
        responses={
            201: openapi.Response(
                description="Admission request created",
                schema=AdmissionRequestSerializer(),
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
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def create(self, request):
        serializer = AdmissionRequestSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            try:
                admission_request = AdmissionService.create_admission_request(
                    user=request.user,
                    institution_id=serializer.validated_data["institution_id"],
                )
                return Response(
                    AdmissionRequestSerializer(admission_request).data,
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as e:
                logger.error(f"Admission request creation error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected admission request creation error: {str(e)}")
                return Response(
                    {"error": "Failed to create admission request"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="List admission requests",
        operation_description="""
        Lists admission requests. For institution admins, shows all requests for their institution.
        For admission seekers, shows their own requests.
        """,
        responses={
            200: openapi.Response(
                description="List of admission requests",
                schema=AdmissionRequestSerializer(many=True),
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
    def list(self, request):
        queryset = self.get_queryset()
        serializer = AdmissionRequestSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Approve an admission request",
        operation_description="""
        Allows an institution admin to approve an admission request, creating an InstitutionMembership
        with role 'student' and setting is_student=True for the user.
        """,
        request_body=AdmissionActionSerializer,
        responses={
            200: openapi.Response(
                description="Admission request approved",
                schema=AdmissionRequestSerializer(),
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        try:
            admission_request = AdmissionService.approve_admission_request(
                admin=request.user,
                request_id=pk,
            )
            return Response(
                AdmissionRequestSerializer(admission_request).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Admission request approval error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected admission request approval error: {str(e)}")
            return Response(
                {"error": "Failed to approve admission request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        operation_summary="Reject an admission request",
        operation_description="""
        Allows an institution admin to reject an admission request.
        """,
        request_body=AdmissionActionSerializer,
        responses={
            200: openapi.Response(
                description="Admission request rejected",
                schema=AdmissionRequestSerializer(),
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        serializer = AdmissionActionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                admission_request = AdmissionService.reject_admission_request(
                    admin=request.user,
                    request_id=pk,
                )
                return Response(
                    AdmissionRequestSerializer(admission_request).data,
                    status=status.HTTP_200_OK,
                )
            except ValidationError as e:
                logger.error(f"Admission request rejection error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected admission request rejection error: {str(e)}")
                return Response(
                    {"error": "Failed to reject admission request"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="List institutions that sent requests to user",
        operation_description="""
        Lists all institutions that sent invitations to the authenticated user (based on email or phone number).
        Includes invitation details like institution name, role, and status (pending, accepted, expired).
        """,
        responses={
            200: openapi.Response(
                description="List of institution invitations",
                schema=InstitutionRequestSerializer(many=True),
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
    @action(detail=False, methods=["get"], url_path="institution-requests")
    def institution_requests(self, request):
        user = request.user
        invitations = Invitation.objects.filter(
            models.Q(email=user.email) | models.Q(phone_number=user.phone_number)
        ).select_related("institution")
        serializer = InstitutionRequestSerializer(invitations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @swagger_auto_schema(
    #     operation_summary="List users who accepted or requested admission",
    #     operation_description="""
    # Lists users who accepted invitations or have admission requests (pending, approved, rejected)
    # for the authenticated admin's institution. Includes user details and request status.
    # Only accessible to institution admins.
    # """,
    #     responses={
    #         200: openapi.Response(
    #             description="List of users and their request statuses",
    #             schema=openapi.Schema(
    #                 type=openapi.TYPE_ARRAY,
    #                 items=openapi.Schema(
    #                     type=openapi.TYPE_OBJECT,
    #                     properties={
    #                         "type": openapi.Schema(
    #                             type=openapi.TYPE_STRING,
    #                             description="Either 'invitation' or 'admission_request'",
    #                         ),
    #                         "user": UserSerializer(),
    #                         "status": openapi.Schema(
    #                             type=openapi.TYPE_STRING,
    #                             description="pending, accepted, approved, rejected, expired",
    #                         ),
    #                         "role": openapi.Schema(
    #                             type=openapi.TYPE_STRING,
    #                             description="Role for invitations, null for admission requests",
    #                             nullable=True,
    #                         ),
    #                         "created_at": openapi.Schema(
    #                             type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
    #                         ),
    #                         "expires_at": openapi.Schema(
    #                             type=openapi.TYPE_STRING,
    #                             format=openapi.FORMAT_DATETIME,
    #                             nullable=True,
    #                         ),
    #                     },
    #                 ),
    #             ),
    #         ),
    #         403: openapi.Response(
    #             description="Forbidden",
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
    @action(detail=False, methods=["get"], url_path="institution-approvals")
    def institution_approvals(self, request):
        user = request.user
        if not user.is_institution:
            return Response(
                {"error": "Only institution admins can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )
        institution = user.admin_institutions.first()
        if not institution:
            return Response(
                {"error": "No institution found for this admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get invitations
        invitations = Invitation.objects.filter(institution=institution).select_related(
            "institution"
        )
        invitation_data = [
            {
                "type": "invitation",
                "user": (
                    UserSerializer(
                        User.objects.filter(
                            models.Q(email=inv.email)
                            | models.Q(phone_number=inv.phone_number)
                        ).first()
                    ).data
                    if (inv.email or inv.phone_number)
                    else None
                ),
                "status": InstitutionRequestSerializer().get_status(inv),
                "role": inv.role,
                "created_at": inv.created_at,
                "expires_at": inv.expires_at,
            }
            for inv in invitations
        ]

        # Get admission requests
        admission_requests = AdmissionRequest.objects.filter(
            institution=institution
        ).select_related("user")
        admission_data = [
            {
                "type": "admission_request",
                "user": UserSerializer(req.user).data,
                "status": req.status,
                "role": None,
                "created_at": req.created_at,
                "expires_at": None,
            }
            for req in admission_requests
        ]

        # Combine and sort by created_at
        combined_data = sorted(
            invitation_data + admission_data,
            key=lambda x: x["created_at"],
            reverse=True,
        )
        return Response(combined_data, status=status.HTTP_200_OK)
