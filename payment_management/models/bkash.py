from django.db import models


class BkashPayment(models.Model):
    payment_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    order_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, default="pending"
    )  # e.g., pending, completed, failed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bkash Payment - {self.order_id} - {self.status}"
