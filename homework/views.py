from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from user_management.serializers.authentication import UserSerializer
from .models import Homework, HomeworkSubmission
from .serializers import (
    HomeworkSerializer,
    HomeworkSubmissionSerializer,
    HomeworkStatisticsSerializer,
)
from user_management.permissions.authentication import IsTeacher
from institution.models import InstitutionInfo, Section, Subject
from user_management.models.authentication import InstitutionMembership
from django.db.models import Q, Count, Case, When, IntegerField

from django.contrib.auth import get_user_model

User = get_user_model()


class HomeworkViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            # Teachers see homework they created or are enrolled to teach
            return Homework.objects.filter(
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
            # Students see homework for their enrolled sections
            return Homework.objects.filter(
                institution__student_enrollments__user=user,
                curriculum_track__student_enrollments__user=user,
                section__student_enrollments__user=user,
                is_active=True,
            )
        elif user.is_institution:
            # Admins see all homework in their institution
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return Homework.objects.filter(institution=institution, is_active=True)
            return Homework.objects.none()
        else:
            # Other members see homework from institutions they are part of
            memberships = InstitutionMembership.objects.filter(user=user)
            institution_ids = memberships.values_list("institution_id", flat=True)
            return Homework.objects.filter(
                institution__id__in=institution_ids, is_active=True
            )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance.created_by != self.request.user:
            return Response(
                {"error": "Only the creator can update this homework."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer.save()


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return HomeworkSubmission.objects.filter(
                homework__institution__teacher_enrollments__user=user,
                homework__curriculum_track__teacher_enrollments__user=user,
                homework__section__teacher_enrollments__user=user,
                homework__subject__teacher_enrollments__user=user,
            ).distinct()
        return HomeworkSubmission.objects.none()

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(
        detail=False,
        methods=["get"],
        url_path="statistics/(?P<section_id>[^/.]+)/(?P<subject_id>[^/.]+)",
    )
    def statistics(self, request, section_id=None, subject_id=None):
        user = request.user
        if not user.is_teacher:
            return Response(
                {"error": "Only teachers can view statistics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            section = Section.objects.get(id=section_id)
            subject = Subject.objects.get(id=subject_id)
        except (Section.DoesNotExist, Subject.DoesNotExist):
            return Response(
                {"error": "Invalid section or subject."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate teacher enrollment
        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=section.curriculum_track
        ).first()
        if not user.teacher_enrollments.filter(
            institution=institution,
            curriculum_track=section.curriculum_track,
            section=section,
            subjects=subject,
        ).exists():
            return Response(
                {
                    "error": "You are not enrolled to teach this subject in this section."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get students in the section
        students = User.objects.filter(
            is_student=True,
            student_enrollments__institution=institution,
            student_enrollments__curriculum_track=section.curriculum_track,
            student_enrollments__section=section,
        ).distinct()

        # Get total homeworks for the section and subject
        total_homeworks = Homework.objects.filter(
            section=section, subject=subject, is_active=True
        ).count()

        # Calculate statistics
        stats = []
        for student in students:
            submissions = HomeworkSubmission.objects.filter(
                homework__section=section,
                homework__subject=subject,
                student=student,
            ).aggregate(
                submitted=Count(
                    Case(
                        When(submitted=True, then=1),
                        output_field=IntegerField(),
                    )
                )
            )
            submitted = submissions["submitted"] or 0
            not_submitted = total_homeworks - submitted
            stats.append(
                {
                    "student": UserSerializer(student).data,
                    "total_homeworks": total_homeworks,
                    "submitted": submitted,
                    "not_submitted": not_submitted,
                }
            )

        serializer = HomeworkStatisticsSerializer(stats, many=True)
        return Response(serializer.data)
