from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from user_management.utils.third_party_api import sms_api
import logging

logger = logging.getLogger("user_management")
redis_client = settings.REDIS_CLIENT


def can_request_invitation(identifier):
    """Check if user can request a new invitation based on cooldown."""
    cooldown_key = f"invitation_cooldown:{identifier}"
    if redis_client.exists(cooldown_key):
        logger.warning(f"Invitation request cooldown active for {identifier}")
        return False
    redis_client.setex(cooldown_key, settings.OTP_REQUEST_COOLDOWN, "1")
    logger.info(f"Invitation cooldown set for {identifier}")
    return True


def send_invitation(identifier, invitation_token, role, institution_name):
    """Send invitation via email or SMS based on identifier type."""
    if not can_request_invitation(identifier):
        raise ValueError("Please wait before sending another invitation.")

    invitation_link = (
        f"http://localhost:8000/auth/invitations/accept/?token={invitation_token}"
    )
    if "@" in identifier:
        # Send invitation via email
        subject = f"Invitation to Join {institution_name} as {role.capitalize()}"
        message = render_to_string(
            "invitation_email.html",
            {
                "role": role.capitalize(),
                "institution_name": institution_name,
                "invitation_link": invitation_link,
                "expiry_days": 7,
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
            logger.info(f"Invitation email sent to {identifier}")
        except Exception as e:
            logger.error(f"Failed to send invitation email to {identifier}: {str(e)}")
            raise ValueError(f"Email sending failed: {str(e)}")
    else:
        # Send invitation via SMS
        message = f"(educational_management) You are invited to join {institution_name} as a {role}. Accept here: {invitation_link}. Expires in 7 days."
        response = sms_api(identifier, message)
        if "error" in response:
            logger.error(f"SMS sending failed for {identifier}: {response['error']}")
            raise ValueError(f"SMS sending failed: {response['error']}")
        if response.get("status") == "Failed":
            logger.error(
                f"SMS sending failed for {identifier}: {response.get('responseResult')}"
            )
            raise ValueError(f"SMS sending failed: {response.get('responseResult')}")
