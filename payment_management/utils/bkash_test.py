import requests
from django.conf import settings


class BkashAPI:
    def __init__(self):
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD
        self.base_url = settings.BKASH_BASE_URL
        self.token = self.get_token()

    def get_token(self):
        url = f"{self.base_url}/tokenized/checkout/token/grant"
        headers = {
            "Content-Type": "application/json",
            "username": self.username,
            "password": self.password,
        }
        data = {"app_key": self.app_key, "app_secret": self.app_secret}
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json().get("id_token")
        except requests.RequestException as e:
            print(f"Token request failed: {str(e)}")
            return None
        except ValueError as e:
            print(f"JSON decode error: {str(e)}")
            return None

    def create_payment(self, amount, invoice):
        url = f"{self.base_url}/tokenized/checkout/create"
        headers = {
            "Content-Type": "application/json",
            "authorization": self.token,
            "x-app-key": self.app_key,
        }
        data = {
            "mode": "0011",
            "payerReference": " ",
            "callbackURL": settings.BKASH_CALLBACK_URL,
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": invoice,
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Payment creation failed: {str(e)}")
            return {"statusMessage": str(e)}

    def execute_payment(self, payment_id):
        url = f"{self.base_url}/tokenized/checkout/execute"
        headers = {
            "Content-Type": "application/json",
            "authorization": self.token,
            "x-app-key": self.app_key,
        }
        try:
            response = requests.post(
                url, headers=headers, json={"paymentID": payment_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Payment execution failed: {str(e)}")
            return {"statusMessage": str(e)}

    def query_payment(self, payment_id):
        url = f"{self.base_url}/tokenized/checkout/payment/status"
        headers = {
            "Content-Type": "application/json",
            "authorization": self.token,
            "x-app-key": self.app_key,
        }
        try:
            response = requests.post(
                url, headers=headers, json={"paymentID": payment_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Payment query failed: {str(e)}")
            return {"statusMessage": str(e)}
