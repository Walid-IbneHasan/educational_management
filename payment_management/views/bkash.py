from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from payment_management.serializers.bkash import PaymentCreateSerializer
from payment_management.utils.bkash import BkashAPI


class BkashCreatePaymentView(APIView):
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            bkash = BkashAPI()
            result = bkash.create_payment(
                amount=serializer.validated_data["amount"],
                invoice=serializer.validated_data["invoice"],
            )
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BkashExecutePaymentView(APIView):
    def post(self, request):
        payment_id = request.data.get("paymentID")
        if not payment_id:
            return Response({"error": "paymentID is required"}, status=400)
        bkash = BkashAPI()
        result = bkash.execute_payment(payment_id)
        return Response(result)


class BkashQueryPaymentView(APIView):
    def post(self, request):
        payment_id = request.data.get("paymentID")
        if not payment_id:
            return Response({"error": "paymentID is required"}, status=400)
        bkash = BkashAPI()
        result = bkash.query_payment(payment_id)
        return Response(result)
