from datetime import timedelta
import logging
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from institution.models import InstitutionInfo
from user_management.models.authentication import (
    ParentChildRelationship,
    User,
    InstitutionMembership,
    Invitation,
)
from user_management.utils.otp import (
    generate_otp,
    store_otp,
    get_otp,
    delete_otp,
    send_otp,
)
from user_management.utils.invitation import send_invitation
from django.utils import timezone
import redis
from django.conf import settings

logger = logging.getLogger("user_management")

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def register_user(email=None, phone_number=None, password=None, role=None):
        logger.info(
            f"Registering user: email={email}, phone_number={phone_number}, role={role}"
        )
        try:
            if not (email or phone_number):
                raise ValidationError("Either email or phone number must be provided.")

            identifier = email or phone_number
            redis_key = f"otp_cooldown:{identifier}"

            last_sent = redis_client.get(redis_key)
            if last_sent:
                last_sent_time = float(last_sent)
                current_time = timezone.now().timestamp()
                if current_time - last_sent_time < 120:
                    raise ValidationError(
                        f"Please wait {120 - int(current_time - last_sent_time)} seconds before requesting a new OTP."
                    )

            user = None
            if email:
                user = User.objects.filter(email=email).first()
            elif phone_number:
                user = User.objects.filter(phone_number=phone_number).first()

            if user:
                if user.is_active:
                    raise ValidationError(
                        f"{'Email' if email else 'Phone number'} already exists."
                    )
                user.password = make_password(password)
                if role == "institution":
                    user.is_institution = True
                    user.is_admission_seeker = False
                else:
                    user.is_institution = False
                    user.is_admission_seeker = True
                user.save()
                logger.info(
                    f"Reusing inactive user: id={user.id}, email={user.email}, phone_number={user.phone_number}"
                )
            else:
                user_data = {
                    "id": uuid.uuid4(),
                    "email": email,
                    "phone_number": phone_number,
                    "password": make_password(password),
                    "is_active": False,
                }
                if role == "institution":
                    user_data.update(
                        {
                            "is_institution": True,
                            "is_admission_seeker": False,
                        }
                    )
                else:
                    user_data.update(
                        {
                            "is_admission_seeker": True,
                        }
                    )
                user = User.objects.create(**user_data)
                logger.info(
                    f"User created: id={user.id}, email={user.email}, phone_number={user.phone_number}"
                )

            otp = generate_otp()
            store_otp(identifier, otp)
            send_otp(identifier, otp, otp_for="account verification")
            redis_client.setex(redis_key, 120, timezone.now().timestamp())
            return user, otp

        except ValueError as e:
            logger.error(f"OTP sending error during registration: {str(e)}")
            raise ValidationError(str(e))
        except redis.RedisError as e:
            logger.error(f"Redis error during OTP storage: {str(e)}")
            raise ValidationError("Failed to store OTP")
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def verify_otp(identifier, otp):
        logger.info(f"Verifying OTP: identifier={identifier}, otp={otp}")
        try:
            user = None
            if "@" in identifier:
                user = User.objects.filter(email=identifier).first()
            else:
                # Normalize phone number for lookup
                phone_number = identifier
                if phone_number.startswith("+880"):
                    phone_number = "0" + phone_number[4:]
                user = User.objects.filter(phone_number=phone_number).first()

            if not user:
                logger.error(f"No user found for identifier: {identifier}")
                raise ValidationError("User not found")

            if user.is_active:
                logger.info(f"User {user.id} is already active")
                raise ValidationError("User is already active")

            stored_otp = get_otp(identifier)
            if not stored_otp:
                logger.error(f"OTP expired or not found for {identifier}")
                raise ValidationError("OTP has expired or is invalid")

            if stored_otp != otp:
                logger.error(f"Invalid OTP for {identifier}")
                raise ValidationError("Invalid OTP")

            user.is_active = True
            user.save()
            logger.info(f"User activated: id={user.id}")

            delete_otp(identifier)
            refresh = RefreshToken.for_user(user)
            tokens = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
            return user, tokens

        except redis.RedisError as e:
            logger.error(f"Redis error during OTP verification: {str(e)}")
            raise ValidationError("Failed to verify OTP")
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def check_user(email=None, phone_number=None):
        logger.info(f"Checking user: email={email}, phone_number={phone_number}")
        try:
            user = None
            if email:
                user = User.objects.filter(email=email).first()
            elif phone_number:
                if phone_number.startswith("+880"):
                    phone_number = "0" + phone_number[4:]
                user = User.objects.filter(phone_number=phone_number).first()

            if user:
                logger.info(f"User found: id={user.id}, is_active={user.is_active}")
                return {"exists": True, "is_active": user.is_active}
            logger.info("No user found")
            return {"exists": False, "is_active": None}

        except Exception as e:
            logger.error(f"Error checking user: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def generate_and_send_otp(identifier):
        logger.info(f"Generating OTP for identifier: {identifier}")
        try:
            user = None
            if "@" in identifier:
                user = User.objects.filter(email=identifier).first()
            else:
                phone_number = identifier
                if phone_number.startswith("+880"):
                    phone_number = "0" + phone_number[4:]
                user = User.objects.filter(phone_number=phone_number).first()

            if not user:
                logger.error(f"No user found for identifier: {identifier}")
                raise ValidationError("User not found")

            otp = generate_otp()
            store_otp(identifier, otp)
            send_otp(identifier, otp, otp_for="password reset")
            return otp

        except ValueError as e:
            logger.error(f"OTP sending error: {str(e)}")
            raise ValidationError(str(e))
        except redis.RedisError as e:
            logger.error(f"Redis error during OTP storage: {str(e)}")
            raise ValidationError("Failed to store OTP")
        except Exception as e:
            logger.error(f"Error generating OTP: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def verify_otp_and_reset_password(identifier, otp, new_password):
        logger.info(f"Resetting password: identifier={identifier}, otp={otp}")
        try:
            user = None
            if "@" in identifier:
                user = User.objects.filter(email=identifier).first()
            else:
                phone_number = identifier
                if phone_number.startswith("+880"):
                    phone_number = "0" + phone_number[4:]
                user = User.objects.filter(phone_number=phone_number).first()

            if not user:
                logger.error(f"No user found for identifier: {identifier}")
                raise ValidationError("User not found")

            stored_otp = get_otp(identifier)
            if not stored_otp:
                logger.error(f"OTP expired or not found for {identifier}")
                raise ValidationError("OTP has expired or is invalid")

            if stored_otp != otp:
                logger.error(f"Invalid OTP for {identifier}")
                raise ValidationError("Invalid OTP")

            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset for user: id={user.id}")

            delete_otp(identifier)
            return user

        except redis.RedisError as e:
            logger.error(f"Redis error during OTP verification: {str(e)}")
            raise ValidationError("Failed to verify OTP")
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def change_password(user, old_password, new_password):
        logger.info(f"Changing password for user: id={user.id}")
        try:
            if not user.check_password(old_password):
                raise ValidationError("Current password is incorrect")

            user.set_password(new_password)
            user.save()
            logger.info(f"Password changed for user: id={user.id}")
            return user

        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def create_institution(
        user, name, institution_type=None, address=None, short_code=None
    ):
        logger.info(f"Creating institution: name={name}, admin_id={user.id}")
        try:
            if not user.is_institution:
                raise ValidationError("User must be an institution admin")

            institution = InstitutionInfo.objects.create(
                name=name,
                institution_type=institution_type,
                address=address,
                short_code=short_code,
                admin=user,
            )

            InstitutionMembership.objects.create(
                user=user,
                institution=institution,
                role="admin",
            )

            logger.info(f"Institution created: id={institution.id}")
            return institution

        except Exception as e:
            logger.error(f"Error creating institution: {str(e)}")
            raise

    @staticmethod
    def create_invitation(email=None, phone_number=None, role=None, admin=None):
        logger.info(
            f"Creating invitation: email={email}, phone_number={phone_number}, role={role}"
        )
        try:
            if not admin.is_institution:
                raise ValidationError("Only institution admins can create invitations")

            institution = InstitutionInfo.objects.filter(admin=admin).first()
            if not institution:
                raise ValidationError("Institution not found for this admin")

            # Normalize phone number
            if phone_number and phone_number.startswith("+880"):
                phone_number = "0" + phone_number[4:]

            invitation = Invitation.objects.create(
                email=email,
                phone_number=phone_number,
                institution=institution,
                role=role,
                token=uuid.uuid4(),
                expires_at=timezone.now() + timedelta(days=7),
            )

            identifier = email or phone_number
            send_invitation(identifier, invitation.token, role, institution.name)
            logger.info(f"Invitation created: token={invitation.token}")
            return invitation

        except ValueError as e:
            logger.error(f"Invitation sending error: {str(e)}")
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error creating invitation: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def accept_invitation(user, token):
        logger.info(f"Accepting invitation: user_id={user.id}, token={token}")
        try:
            invitation = Invitation.objects.filter(token=token, is_used=False).first()
            if not invitation:
                logger.error(f"Invalid or used invitation: token={token}")
                raise ValidationError("Invalid or expired invitation")

            logger.debug(
                f"Comparing expires_at={invitation.expires_at} with now={timezone.now()}"
            )
            if invitation.expires_at < timezone.now():
                logger.error(
                    f"Invitation expired: token={token}, expires_at={invitation.expires_at}"
                )
                raise ValidationError("Invitation has expired")

            if (invitation.email and invitation.email != user.email) or (
                invitation.phone_number and invitation.phone_number != user.phone_number
            ):
                logger.error(
                    f"Invitation mismatch: user_email={user.email}, user_phone={user.phone_number}"
                )
                raise ValidationError("Invitation does not match user credentials")

            InstitutionMembership.objects.create(
                user=user,
                institution=invitation.institution,
                role=invitation.role,
            )

            if invitation.role == "teacher":
                user.is_teacher = True
            elif invitation.role == "student":
                user.is_student = True
                user.is_admission_seeker = False

            user.save()
            invitation.is_used = True
            invitation.save()

            logger.info(
                f"Invitation accepted: user_id={user.id}, institution_id={invitation.institution.id}"
            )
            return invitation

        except Exception as e:
            logger.error(f"Error accepting invitation: {str(e)}")
            raise ValidationError(str(e))

    @staticmethod
    def create_parent_child_relationship(parent, child_id):
        logger.info(
            f"Creating parent-child relationship: parent_id={parent.id}, child_id={child_id}"
        )
        try:
            child = User.objects.filter(id=child_id, is_student=True).first()
            if not child:
                raise ValidationError("Child not found or not a student")

            relationship = ParentChildRelationship.objects.create(
                parent=parent,
                child=child,
            )

            parent.is_parents = True
            parent.save()

            logger.info(f"Parent-child relationship created: id={relationship.id}")
            return relationship

        except Exception as e:
            logger.error(f"Error creating parent-child relationship: {str(e)}")
            raise ValidationError(str(e))
