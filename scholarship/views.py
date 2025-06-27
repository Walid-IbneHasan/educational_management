from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from user_management.permissions.authentication import IsInstitutionAdmin
from .models import Scholarship
from .serializers import ScholarshipSerializer
from institution.models import InstitutionInfo
from rest_framework.exceptions import ValidationError


class ScholarshipViewSet(viewsets.ModelViewSet):
    serializer_class = ScholarshipSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return Scholarship.objects.none()
        return Scholarship.objects.filter(institution=institution)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if institution:
            context["institution"] = institution
        return context

    def perform_create(self, serializer):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            raise ValidationError("No institution found for this admin.")
        serializer.save(institution=institution)
