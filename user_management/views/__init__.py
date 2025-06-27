from user_management.views.authentication import (
    CustomTokenObtainPairView,
    UserViewSet,
    InstitutionViewSet,
    InstitutionMembershipViewSet,
    InvitationViewSet,
    ParentChildRelationshipViewSet,
    VerifyOTPView,
)
from user_management.views.user_info import UserInfoView
from user_management.views.admission_seeker import AdmissionRequestViewSet

__all__ = [
    "UserViewSet",
    "InstitutionViewSet",
    "InstitutionMembershipViewSet",
    "InvitationViewSet",
    "ParentChildRelationshipViewSet",
    "VerifyOTPView",
    "CustomTokenObtainPairView",
    "UserInfoView",
    "AdmissionRequestViewSet",
]
