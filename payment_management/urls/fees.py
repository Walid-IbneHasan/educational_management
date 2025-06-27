from django.urls import path
from payment_management.views.fees import (
    StudentFeePaymentViewSet,
    InstitutionPaymentTrackerViewSet,
)

urlpatterns = [
    path(
        "fee-payments/",
        StudentFeePaymentViewSet.as_view({"get": "list", "post": "create"}),
        name="fee-payment-list",
    ),
    path(
        "fee-payments/<uuid:pk>/",
        StudentFeePaymentViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="fee-payment-detail",
    ),
    path(
        "payment-trackers/",
        InstitutionPaymentTrackerViewSet.as_view({"get": "list"}),
        name="payment-tracker-list",
    ),
    path(
        "payment-trackers/<uuid:pk>/",
        InstitutionPaymentTrackerViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="payment-tracker-detail",
    ),
]
