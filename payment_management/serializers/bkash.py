from rest_framework import serializers


class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    invoice = serializers.CharField()
