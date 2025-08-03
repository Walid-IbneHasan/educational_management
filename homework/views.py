from uuid import UUID
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
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model

User = get_user_model()


class HomeworkViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            queryset = Homework.objects.filter(is_active=True)
            if institution_id:
                try:
                    UUID(institution_id)
                except ValueError:
                    return Response(
                        {"error": "Invalid UUID format for institution ID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not InstitutionMembership.objects.filter(
                    user=user, institution__id=institution_id, role="teacher"
                ).exists():
                    return Response(
                        {"error": "You are not enrolled in this institution."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                queryset = queryset.filter(institution__id=institution_id)
            # Filter by teacher enrollment for section and subject
            queryset = queryset.filter(
                curriculum_track__teacher_enrollments__user=user,
                section__teacher_enrollments__user=user,
                subject__teacher_enrollments__user=user,
            ).distinct()
            if not queryset.exists():
                # Provide detailed error for debugging
                error_details = {
                    "detail": "No Homework matches the given query.",
                    "debug_info": {
                        "institution_id": institution_id,
                        "user_phone": user.phone_number,
                        "enrollment_check": "No active TeacherEnrollment found for this user in the specified institution, curriculum track, section, and subject.",
                    },
                }
                if institution_id:
                    error_details["debug_info"]["suggestion"] = (
                        f"Verify TeacherEnrollment for user {user.phone_number} with institution_id={institution_id}, "
                        "and ensure curriculum_track, section, and subject are correctly associated."
                    )
                return Response(error_details, status=status.HTTP_404_NOT_FOUND)
            return queryset
        elif user.is_student:
            return Homework.objects.filter(
                institution__student_enrollments__user=user,
                curriculum_track__student_enrollments__user=user,
                section__student_enrollments__user=user,
                is_active=True,
            )
        elif user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return Homework.objects.filter(institution=institution, is_active=True)
            return Homework.objects.none()
        else:
            memberships = InstitutionMembership.objects.filter(user=user)
            institution_ids = memberships.values_list("institution_id", flat=True)
            return Homework.objects.filter(
                institution__id__in=institution_ids, is_active=True
            )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                context["institution"] = institution
        elif user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if institution_id:
                try:
                    UUID(institution_id)
                    institution = InstitutionInfo.objects.filter(
                        id=institution_id
                    ).first()
                    if (
                        institution
                        and InstitutionMembership.objects.filter(
                            user=user, institution=institution, role="teacher"
                        ).exists()
                    ):
                        context["institution"] = institution
                    else:
                        raise ValidationError(
                            {
                                "institution_id": "You are not enrolled in this institution."
                            }
                        )
                except ValueError:
                    raise ValidationError(
                        {"institution_id": "Invalid UUID format for institution ID."}
                    )
        return context

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                raise ValidationError("No institution found for this admin.")
            serializer.save()
        elif user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if (
                not institution
                or not InstitutionMembership.objects.filter(
                    user=user, institution=institution, role="teacher"
                ).exists()
            ):
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            curriculum_track = serializer.validated_data["curriculum_track"]
            if curriculum_track.institution_info != institution:
                raise ValidationError(
                    {
                        "curriculum_track": "Curriculum track does not belong to the specified institution."
                    }
                )
            serializer.save(created_by=user)

    def perform_update(self, serializer):
        if serializer.instance.created_by != self.request.user:
            return Response(
                {"error": "Only the creator can update this homework."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user = self.request.user
        if user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if (
                not institution
                or not InstitutionMembership.objects.filter(
                    user=user, institution=institution, role="teacher"
                ).exists()
            ):
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            curriculum_track = serializer.validated_data["curriculum_track"]
            if curriculum_track.institution_info != institution:
                raise ValidationError(
                    {
                        "curriculum_track": "Curriculum track does not belong to the specified institution."
                    }
                )
        serializer.save()

    @action(
        detail=False,
        methods=["get"],
        url_path="submissions/(?P<homework_id>[^/.]+)",
    )
    def homework_submissions(self, request, homework_id=None):
        user = request.user
        try:
            UUID(homework_id)
        except ValueError:
            raise ValidationError(
                {"homework_id": "Invalid UUID format for homework ID."}
            )

        try:
            homework = Homework.objects.get(id=homework_id, is_active=True)
        except Homework.DoesNotExist:
            return Response(
                {"error": "Homework does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_teacher:
            institution_id = request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if not institution:
                raise ValidationError({"institution_id": "Institution does not exist."})
            if not InstitutionMembership.objects.filter(
                user=user, institution=institution, role="teacher"
            ).exists():
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            if homework.institution != institution:
                return Response(
                    {"error": "Homework does not belong to the specified institution."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not user.teacher_enrollments.filter(
                institution=institution,
                curriculum_track=homework.curriculum_track,
                section=homework.section,
                subjects=homework.subject,
                is_active=True,
            ).exists():
                return Response(
                    {
                        "error": "You are not enrolled to teach this homework's subject in this section."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return Response(
                    {"error": "No institution found for this admin."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if homework.institution != institution:
                return Response(
                    {"error": "Homework does not belong to your institution."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"error": "Only teachers or institution admins can view submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        submissions = HomeworkSubmission.objects.filter(
            homework=homework, submitted=True
        )
        total_submissions = submissions.count()
        serializer = HomeworkSubmissionSerializer(submissions, many=True)

        return Response(
            {
                "homework_id": homework_id,
                "total_submissions": total_submissions,
                "submissions": serializer.data,
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="assigned/(?P<section_id>[^/.]+)/(?P<subject_id>[^/.]+)",
    )
    def assigned(self, request, section_id=None, subject_id=None):
        user = request.user
        if not user.is_teacher and not user.is_institution:
            return Response(
                {
                    "error": "Only teachers or institution admins can view assigned homework."
                },
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

        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=section.curriculum_track
        ).first()
        if not institution:
            return Response(
                {"error": "No institution found for this section."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_institution:
            if institution.admin != user:
                return Response(
                    {"error": "You are not the admin of this institution."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif user.is_teacher:
            institution_id = request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            if institution_id != str(institution.id):
                raise ValidationError(
                    {
                        "institution_id": "Section does not belong to the specified institution."
                    }
                )
            if not InstitutionMembership.objects.filter(
                user=user, institution=institution, role="teacher"
            ).exists():
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            if not user.teacher_enrollments.filter(
                institution=institution,
                curriculum_track=section.curriculum_track,
                section=section,
                subjects=subject,
                is_active=True,
            ).exists():
                return Response(
                    {
                        "error": "You are not enrolled to teach this subject in this section."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Filter homework by section, subject, and created_by (for teachers)
        queryset = Homework.objects.filter(
            institution=institution,
            section=section,
            subject=subject,
            created_by=user,
            is_active=True,
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if institution_id:
                try:
                    UUID(institution_id)
                except ValueError:
                    raise ValidationError(
                        {"institution_id": "Invalid UUID format for institution ID."}
                    )
                if not InstitutionMembership.objects.filter(
                    user=user, institution__id=institution_id, role="teacher"
                ).exists():
                    raise ValidationError(
                        {"institution_id": "You are not enrolled in this institution."}
                    )
                return HomeworkSubmission.objects.filter(
                    homework__institution__id=institution_id,
                    homework__curriculum_track__teacher_enrollments__user=user,
                    homework__section__teacher_enrollments__user=user,
                    homework__subject__teacher_enrollments__user=user,
                ).distinct()
            return HomeworkSubmission.objects.filter(
                homework__institution__teacher_enrollments__user=user,
                homework__curriculum_track__teacher_enrollments__user=user,
                homework__section__teacher_enrollments__user=user,
                homework__subject__teacher_enrollments__user=user,
            ).distinct()
        elif user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                return HomeworkSubmission.objects.filter(
                    homework__institution=institution
                ).distinct()
            return HomeworkSubmission.objects.none()
        return HomeworkSubmission.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                context["institution"] = institution
        elif user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if institution_id:
                try:
                    UUID(institution_id)
                    institution = InstitutionInfo.objects.filter(
                        id=institution_id
                    ).first()
                    if (
                        institution
                        and InstitutionMembership.objects.filter(
                            user=user, institution=institution, role="teacher"
                        ).exists()
                    ):
                        context["institution"] = institution
                    else:
                        raise ValidationError(
                            {
                                "institution_id": "You are not enrolled in this institution."
                            }
                        )
                except ValueError:
                    raise ValidationError(
                        {"institution_id": "Invalid UUID format for institution ID."}
                    )
        return context

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                raise ValidationError("No institution found for this admin.")
            serializer.save()
        elif user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if (
                not institution
                or not InstitutionMembership.objects.filter(
                    user=user, institution=institution, role="teacher"
                ).exists()
            ):
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            homework = serializer.validated_data["homework"]
            if homework.institution != institution:
                raise ValidationError(
                    {
                        "homework": "Homework does not belong to the specified institution."
                    }
                )
            serializer.save(updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                raise ValidationError("No institution found for this admin.")
            serializer.save()
        elif user.is_teacher:
            institution_id = self.request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            institution = InstitutionInfo.objects.filter(id=institution_id).first()
            if (
                not institution
                or not InstitutionMembership.objects.filter(
                    user=user, institution=institution, role="teacher"
                ).exists()
            ):
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            homework = serializer.validated_data["homework"]
            if homework.institution != institution:
                raise ValidationError(
                    {
                        "homework": "Homework does not belong to the specified institution."
                    }
                )
            serializer.save(updated_by=user)

    @action(
        detail=False,
        methods=["get"],
        url_path="statistics/(?P<section_id>[^/.]+)/(?P<subject_id>[^/.]+)",
    )
    def statistics(self, request, section_id=None, subject_id=None):
        user = request.user
        if not user.is_teacher and not user.is_institution:
            return Response(
                {"error": "Only teachers or institution admins can view statistics."},
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

        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=section.curriculum_track
        ).first()
        if not institution:
            return Response(
                {"error": "No institution found for this section."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_institution:
            if institution.admin != user:
                return Response(
                    {"error": "You are not the admin of this institution."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif user.is_teacher:
            institution_id = request.query_params.get("institution_id")
            if not institution_id:
                raise ValidationError(
                    {"institution_id": "Institution ID is required for teachers."}
                )
            try:
                UUID(institution_id)
            except ValueError:
                raise ValidationError(
                    {"institution_id": "Invalid UUID format for institution ID."}
                )
            if institution_id != str(institution.id):
                raise ValidationError(
                    {
                        "institution_id": "Section does not belong to the specified institution."
                    }
                )
            if not InstitutionMembership.objects.filter(
                user=user, institution=institution, role="teacher"
            ).exists():
                raise ValidationError(
                    {"institution_id": "You are not enrolled in this institution."}
                )
            if not user.teacher_enrollments.filter(
                institution=institution,
                curriculum_track=section.curriculum_track,
                section=section,
                subjects=subject,
                is_active=True,
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
            institution=institution, section=section, subject=subject, is_active=True
        ).count()

        # Calculate statistics
        stats = []
        for student in students:
            submissions = HomeworkSubmission.objects.filter(
                homework__section=section,
                homework__subject=subject,
                homework__institution=institution,
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
