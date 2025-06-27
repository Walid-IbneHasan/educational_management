from django.db import transaction
from django.core.exceptions import ValidationError
import logging
from institution.models import InstitutionInfo
from user_management.models.admission_seeker import AdmissionRequest
from user_management.models.authentication import (
    InstitutionMembership,
    User,
)
from django.utils import timezone

logger = logging.getLogger("user_management")


class AdmissionService:
    @staticmethod
    @transaction.atomic
    def create_admission_request(user, institution_id):
        """
        Creates an admission request for a user to an institution.
        """
        logger.info(
            f"Creating admission request: user_id={user.id}, institution_id={institution_id}"
        )
        try:
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if not institution:
                raise ValidationError("Institution not found")
            if not user.is_admission_seeker:
                raise ValidationError("User is not an admission seeker")
            if AdmissionRequest.objects.filter(
                user=user, institution=institution, status="pending"
            ).exists():
                raise ValidationError(
                    "You already have a pending admission request for this institution"
                )

            request = AdmissionRequest.objects.create(
                user=user,
                institution=institution,
                status="pending",
            )
            logger.info(f"Admission request created: id={request.id}")
            return request
        except Exception as e:
            logger.error(f"Error creating admission request: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    @transaction.atomic
    def approve_admission_request(admin, request_id):
        """
        Approves an admission request, creating an InstitutionMembership.
        """
        logger.info(
            f"Approving admission request: admin_id={admin.id}, request_id={request_id}"
        )
        try:
            if not admin.is_institution:
                raise ValidationError("Only institution admins can approve requests")
            institution = InstitutionInfo.objects.filter(admin=admin).first()
            if not institution:
                raise ValidationError("Institution not found for this admin")

            request = AdmissionRequest.objects.filter(
                id=request_id, institution=institution, status="pending"
            ).first()
            if not request:
                raise ValidationError(
                    "Admission request not found or already processed"
                )

            # Create membership
            membership = InstitutionMembership.objects.create(
                user=request.user,
                institution=request.institution,
                role="student",
            )
            request.user.is_student = True
            request.user.save()
            request.status = "approved"
            request.updated_at = timezone.now()
            request.save()

            logger.info(
                f"Admission request approved: id={request.id}, membership_id={membership.id}"
            )
            return request
        except Exception as e:
            logger.error(f"Error approving admission request: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    @transaction.atomic
    def reject_admission_request(admin, request_id):
        """
        Rejects an admission request.
        """
        logger.info(
            f"Rejecting admission request: admin_id={admin.id}, request_id={request_id}"
        )
        try:
            if not admin.is_institution:
                raise ValidationError("Only institution admins can reject requests")
            institution = InstitutionInfo.objects.filter(admin=admin).first()
            if not institution:
                raise ValidationError("Institution not found for this admin")

            request = AdmissionRequest.objects.filter(
                id=request_id, institution=institution, status="pending"
            ).first()
            if not request:
                raise ValidationError(
                    "Admission request not found or already processed"
                )

            request.status = "rejected"
            request.updated_at = timezone.now()
            request.save()

            logger.info(f"Admission request rejected: id={request.id}")
            return request
        except Exception as e:
            logger.error(f"Error rejecting admission request: {str(e)}")
            raise ValidationError(str(e))
