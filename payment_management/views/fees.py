from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from payment_management.models.bkash import BkashPayment
from payment_management.models.fees import InstitutionPaymentTracker, StudentFeePayment
from payment_management.serializers.fees import (
    InstitutionPaymentTrackerSerializer,
    StudentFeePaymentSerializer,
)
from payment_management.serializers.bkash import PaymentCreateSerializer
from payment_management.utils.bkash_test import BkashAPI  # Use the new bkash_test.py

from institution.models import (
    InstitutionFee,
    CurriculumTrackFee,
    InstitutionInfo,
    StudentFee,
    StudentEnrollment,
)
from scholarship.models import Scholarship
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import logging
import decimal
import requests
from django.conf import settings

from user_management.models.authentication import ParentChildRelationship
from user_management.permissions.authentication import IsInstitutionAdmin

# Set up logging
logger = logging.getLogger(__name__)


class StudentFeePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentFeePaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            return StudentFeePayment.objects.filter(
                student_enrollment__institution=institution
            )
        # Filter for students
        queryset = StudentFeePayment.objects.filter(student_enrollment__user=user)

        # Filter for parents
        child_ids = ParentChildRelationship.objects.filter(parent=user).values_list(
            "child_id", flat=True
        )
        parent_enrollments = StudentEnrollment.objects.filter(user__id__in=child_ids)
        queryset = queryset | StudentFeePayment.objects.filter(
            student_enrollment__in=parent_enrollments
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        student_enrollment = StudentEnrollment.objects.get(
            id=serializer.validated_data["student_enrollment_id"]
        )

        # Calculate fee
        try:
            student_fee = StudentFee.objects.filter(
                student_enrollment=student_enrollment
            ).first()
            if student_fee:
                fee = student_fee.fee
            else:
                curriculum_fee = CurriculumTrackFee.objects.filter(
                    curriculum_track=student_enrollment.curriculum_track
                ).first()
                fee = (
                    curriculum_fee.fee
                    if curriculum_fee
                    else InstitutionFee.objects.get(
                        institution=student_enrollment.institution
                    ).default_fee
                )
        except InstitutionFee.DoesNotExist:
            logger.error(
                f"No default fee set for institution {student_enrollment.institution.id}"
            )
            return Response(
                {"error": "No default fee set for the institution"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply scholarship
        scholarship = Scholarship.objects.filter(
            student_enrollment=student_enrollment, is_active=True
        ).first()
        scholarship_amount = decimal.Decimal("0.00")
        if scholarship:
            scholarship_amount = fee * (scholarship.percentage / decimal.Decimal("100"))
            fee -= scholarship_amount

        # Round fee to 2 decimal places
        fee = fee.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)

        # Create bKash payment
        bkash = BkashAPI()
        invoice = f"FEE-{student_enrollment.id}-{serializer.validated_data['month'].strftime('%Y%m')}"
        payment_data = {"amount": fee, "invoice": invoice}
        payment_serializer = PaymentCreateSerializer(data=payment_data)
        if not payment_serializer.is_valid():
            logger.error(f"Payment serializer error: {payment_serializer.errors}")
            return Response(
                payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Log bKash configuration
            logger.info(
                f"bKash configuration: app_key={settings.BKASH_APP_KEY[:5]}..., username={settings.BKASH_USERNAME}, base_url={settings.BKASH_BASE_URL}"
            )

            # Attempt to get token
            token = bkash.get_token()
            if not token:
                # Manual token request for debugging
                url = f"{settings.BKASH_BASE_URL}/tokenized/checkout/token/grant"
                headers = {
                    "Content-Type": "application/json",
                    "username": settings.BKASH_USERNAME,
                    "password": settings.BKASH_PASSWORD,
                }
                data = {
                    "app_key": settings.BKASH_APP_KEY,
                    "app_secret": settings.BKASH_APP_SECRET,
                }
                try:
                    response = requests.post(url, headers=headers, json=data)
                    logger.error(
                        f"Manual token request response: status={response.status_code}, body={response.text}"
                    )
                    return Response(
                        {
                            "error": f"Failed to authenticate with bKash: {response.text}"
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                except requests.RequestException as e:
                    logger.error(f"Manual token request failed: {str(e)}")
                    return Response(
                        {"error": f"Failed to authenticate with bKash: {str(e)}"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )

            logger.info(f"Obtained bKash token: {token[:10]}...")
            bkash_response = bkash.create_payment(
                amount=payment_serializer.validated_data["amount"],
                invoice=payment_serializer.validated_data["invoice"],
            )
            logger.info(f"bKash create_payment response: {bkash_response}")

            if bkash_response.get("statusCode") != "0000":
                logger.error(f"bKash payment creation failed: {bkash_response}")
                return Response(
                    {
                        "error": bkash_response.get(
                            "statusMessage", "Payment creation failed"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                bkash_payment = BkashPayment.objects.create(
                    payment_id=bkash_response.get("paymentID"),
                    order_id=invoice,
                    amount=fee,
                    status="pending",
                )

                fee_payment = StudentFeePayment.objects.create(
                    student_enrollment=student_enrollment,
                    bkash_payment=bkash_payment,
                    amount=fee,
                    month=serializer.validated_data["month"],
                    scholarship_applied=bool(scholarship),
                    scholarship_amount=scholarship_amount,
                )

                InstitutionPaymentTracker.objects.create(
                    institution=student_enrollment.institution,
                    student_fee_payment=fee_payment,
                    amount=fee,
                )

            return Response(
                {
                    "payment_id": bkash_response.get("paymentID"),
                    "bkash_url": bkash_response.get("bkashURL"),
                    "fee_payment_id": fee_payment.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"bKash API error: {str(e)}")
            return Response(
                {"error": f"Payment creation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InstitutionPaymentTrackerViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionPaymentTrackerSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return InstitutionPaymentTracker.objects.none()
        return InstitutionPaymentTracker.objects.filter(institution=institution)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_disbursed:
            return Response(
                {"error": "Payment already disbursed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.is_disbursed = True
        instance.disbursed_at = timezone.now()
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
