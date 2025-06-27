import requests
from django.conf import settings
import logging
import re

logger = logging.getLogger("user_management")


def format_phone_number(phone_number):
    """
    Formats a phone number to ensure it starts with '880' and is 13 digits long.
    Normalizes inputs like '01886134904', '+8801886134904', '8801886134904' to '8801886134904'.
    """
    phone_number = phone_number.strip().replace("+", "").replace(" ", "")
    logger.debug(f"Raw phone number input: {phone_number}")

    # Remove leading '0' or '88' to get the 10-digit core number
    if phone_number.startswith("880"):
        core_number = phone_number[3:]  # e.g., 8801886134904 -> 1886134904
    elif phone_number.startswith("88"):
        core_number = phone_number[2:]  # e.g., 881886134904 -> 1886134904
    elif phone_number.startswith("0"):
        core_number = phone_number[1:]  # e.g., 01886134904 -> 1886134904
    else:
        core_number = phone_number  # e.g., 1886134904 -> 1886134904
    logger.debug(f"Core number after stripping: {core_number}")

    # Prepend '880' to form the 13-digit number
    formatted_number = "880" + core_number
    logger.debug(f"Formatted phone number: {formatted_number}")

    # Validate the final format
    if not re.match(r"^880\d{10}$", formatted_number):
        logger.error(f"Invalid phone number format: {formatted_number}")
        raise ValueError("Phone number must be 13 digits starting with '880'")

    return formatted_number


def sms_api(phone_number, message):
    """
    Sends an SMS using the MIM SMS API.
    """
    api_url = "https://api.mimsms.com/api/SmsSending/SMS"

    # Format phone number for MIM SMS API
    try:
        formatted_number = format_phone_number(phone_number)
        logger.info(f"Sending SMS to formatted number: {formatted_number}")
    except ValueError as e:
        logger.error(f"Phone number formatting failed: {str(e)}")
        return {"error": str(e)}

    payload = {
        "UserName": settings.SMS_USERNAME,
        "Apikey": settings.SMS_API_KEY,
        "MobileNumber": formatted_number,
        "CampaignId": "null",
        "SenderName": settings.SMS_SENDER_ID,
        "TransactionType": "T",
        "Message": message,
    }
    logger.debug(f"SMS API payload: {payload}")

    try:
        response = requests.post(api_url, json=payload)
        logger.debug(f"SMS API response status code: {response.status_code}")
        logger.debug(f"SMS API response headers: {response.headers}")
        response_json = response.json()
        logger.info(f"SMS API response: {response_json}")

        if response_json.get("status") == "Failed":
            logger.error(
                f"SMS sending failed for {formatted_number}: {response_json.get('responseResult')}"
            )
            return response_json

        response.raise_for_status()
        logger.info(f"SMS sent successfully to {formatted_number}: {response_json}")
        return response_json
    except requests.RequestException as e:
        logger.error(f"SMS sending failed for {formatted_number}: {str(e)}")
        logger.debug(
            f"Full error response: {response.text if 'response' in locals() else 'No response'}"
        )
        return {"error": str(e)}
