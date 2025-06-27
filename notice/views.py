from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Notice
from .serializers import NoticeSerializer
from user_management.permissions.authentication import IsInstitutionAdmin
from institution.models import InstitutionInfo
from user_management.models.authentication import InstitutionMembership


class NoticeViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Institution admins see only their institution's notices
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return Notice.objects.filter(institution=institution)
            return Notice.objects.none()
        # Other members see notices from institutions they are part of
        memberships = InstitutionMembership.objects.filter(user=user)
        institution_ids = memberships.values_list("institution_id", flat=True)
        return Notice.objects.filter(institution__id__in=institution_ids, is_active=True)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsInstitutionAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        institution = InstitutionInfo.objects.filter(admin=request.user).first()
        if not institution:
            return Response(
                {"error": "No institution found for this admin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()