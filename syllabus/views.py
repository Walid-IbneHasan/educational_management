from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Syllabus
from .serializers import SyllabusSerializer
from user_management.permissions.authentication import IsTeacher
from institution.models import InstitutionInfo
from user_management.models.authentication import InstitutionMembership
from django.db.models import Q


class SyllabusViewSet(viewsets.ModelViewSet):
    serializer_class = SyllabusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            # Teachers see syllabi they created or are enrolled to teach
            return Syllabus.objects.filter(
                Q(created_by=user)
                | Q(
                    institution__teacher_enrollments__user=user,
                    curriculum_track__teacher_enrollments__user=user,
                    section__teacher_enrollments__user=user,
                    subject__teacher_enrollments__user=user,
                ),
                is_active=True,
            ).distinct()
        elif user.is_student:
            # Students see syllabi for their enrolled sections
            return Syllabus.objects.filter(
                institution__student_enrollments__user=user,
                curriculum_track__student_enrollments__user=user,
                section__student_enrollments__user=user,
                is_active=True,
            )
        elif user.is_institution:
            # Admins see all syllabi in their institution
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return Syllabus.objects.filter(institution=institution, is_active=True)
            return Syllabus.objects.none()
        else:
            # Other members see syllabi from institutions they are part of
            memberships = InstitutionMembership.objects.filter(user=user)
            institution_ids = memberships.values_list("institution_id", flat=True)
            return Syllabus.objects.filter(
                institution__id__in=institution_ids, is_active=True
            )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        # Ensure only the creator can update
        if serializer.instance.created_by != self.request.user:
            return Response(
                {"error": "Only the creator can update this syllabus."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer.save()
