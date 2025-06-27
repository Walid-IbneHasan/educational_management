from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from user_management.views.authentication import (
    UserInstitutionsViewSet,
    UserViewSet,
    InstitutionViewSet,
    InstitutionMembershipViewSet,
    InvitationViewSet,
    ParentChildRelationshipViewSet,
    VerifyOTPView,
    CustomTokenObtainPairView,
    StudentTeacherViewset,
)
from user_management.views.user_info import UserInfoView

app_name = "authentication"

urlpatterns = [
    path(
        "register/",
        UserViewSet.as_view({"post": "register"}),
        name="user-register",
    ),
    path(
        "users/",
        UserViewSet.as_view({"get": "list"}),
        name="user-list",
    ),
    path(
        "users/check/",
        UserViewSet.as_view({"post": "check"}),
        name="user-check",
    ),
    path(
        "profile/",
        UserViewSet.as_view({"get": "profile", "post": "profile", "patch": "profile"}),
        name="user-profile",
    ),
    path(
        "verify-otp/",
        VerifyOTPView.as_view(),
        name="verify-otp",
    ),
    path(
        "forget-password/",
        UserViewSet.as_view({"post": "forget_password"}),
        name="forget-password",
    ),
    path(
        "reset-password/",
        UserViewSet.as_view({"post": "reset_password"}),
        name="reset-password",
    ),
    path(
        "change-password/",
        UserViewSet.as_view({"post": "change_password"}),
        name="change-password",
    ),
    path(
        "institutions/",
        InstitutionViewSet.as_view({"get": "list", "post": "create"}),
        name="institution-list",
    ),
    path(
        "institutions/<uuid:pk>/",
        InstitutionViewSet.as_view({"get": "retrieve"}),
        name="institution-detail",
    ),
    path(
        "my-institution-memberships/",
        UserInstitutionsViewSet.as_view({"get": "list"}),
        name="user-institutions",
    ),
    path(
        "memberships/",
        InstitutionMembershipViewSet.as_view({"get": "list"}),
        name="membership-list",
    ),
    path(
        "invitations/",
        InvitationViewSet.as_view({"get": "list", "post": "create"}),
        name="invitation-list",
    ),
    path(
        "invitations/accept/",
        InvitationViewSet.as_view({"post": "accept", "get": "accept"}),
        name="invitation-accept",
    ),
    path(
        "parent-child/",
        ParentChildRelationshipViewSet.as_view({"get": "list", "post": "create"}),
        name="parent-child-list",
    ),
    path(
        "institutions/members/",
        StudentTeacherViewset.as_view({"get": "members"}),
        name="institution-members",
    ),
    path(
        "login/",
        CustomTokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "user-info/",
        UserInfoView.as_view(),
        name="user-info",
    ),
]
