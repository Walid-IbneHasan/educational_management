import random
import string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from user_management.utils.third_party_api import sms_api
import logging

logger = logging.getLogger("user_management")
redis_client = settings.REDIS_CLIENT


def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    return "".join(random.choices(string.digits, k=length))


def store_otp(identifier, otp):
    """Store OTP in Redis with expiration."""
    key = f"otp:{identifier}"
    redis_client.setex(key, settings.OTP_EXPIRY_TIME, otp)
    logger.info(f"OTP stored in Redis for {identifier}")


def get_otp(identifier):
    """Retrieve OTP from Redis."""
    key = f"otp:{identifier}"
    return redis_client.get(key)


def delete_otp(identifier):
    """Delete OTP from Redis."""
    key = f"otp:{identifier}"
    redis_client.delete(key)
    logger.info(f"OTP deleted from Redis for {identifier}")


def can_request_otp(identifier):
    """Check if user can request a new OTP based on cooldown."""
    cooldown_key = f"otp_cooldown:{identifier}"
    if redis_client.exists(cooldown_key):
        logger.warning(f"OTP request cooldown active for {identifier}")
        return False
    redis_client.setex(cooldown_key, settings.OTP_REQUEST_COOLDOWN, "1")
    logger.info(f"OTP cooldown set for {identifier}")
    return True


def send_otp(identifier, otp, otp_for="account verification"):
    """Send OTP via email or SMS based on identifier type."""
    if not can_request_otp(identifier):
        raise ValueError("Please wait before requesting a new OTP.")

    if "@" in identifier:
        # Send OTP via email
        subject = "Your Tutoria OTP"
        message = render_to_string(
            "otp_email.html",
            {
                "otp": otp,
                "otp_for": otp_for,
                "expiry_minutes": settings.OTP_EXPIRY_TIME // 60,
            },
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [identifier],
                html_message=message,
            )
            logger.info(f"OTP email sent to {identifier}")
        except Exception as e:
            logger.error(f"Failed to send OTP email to {identifier}: {str(e)}")
            raise ValueError(f"Email sending failed: {str(e)}")
    else:
        # Send OTP via SMS
        message = f"(Tutoria) Your OTP for {otp_for} is {otp}. It expires in {settings.OTP_EXPIRY_TIME // 60} minutes. Do not share this OTP."
        response = sms_api(identifier, message)
        if "error" in response:
            logger.error(f"SMS sending failed for {identifier}: {response['error']}")
            raise ValueError(f"SMS sending failed: {response['error']}")
        if response.get("status") == "Failed":
            logger.error(
                f"SMS sending failed for {identifier}: {response.get('responseResult')}"
            )
            raise ValueError(f"SMS sending failed: {response.get('responseResult')}")
