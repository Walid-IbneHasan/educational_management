from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import Syllabus
from .serializers import SyllabusSerializer
from user_management.permissions.authentication import IsTeacher
from institution.models import InstitutionInfo, Subject
from user_management.models.authentication import InstitutionMembership
from django.db.models import Q
from uuid import UUID


class SyllabusViewSet(viewsets.ModelViewSet):
    serializer_class = SyllabusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        institution_id = self.request.query_params.get("institution_id")
        subject_id = self.request.query_params.get("subject_id")

        if user.is_teacher:
            queryset = Syllabus.objects.filter(
                institution__teacher_enrollments__user=user,
                curriculum_track__teacher_enrollments__user=user,
                section__teacher_enrollments__user=user,
                subject__teacher_enrollments__user=user,
                is_active=True,
            ).distinct()
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
                queryset = queryset.filter(institution__id=institution_id)
            if subject_id:
                try:
                    UUID(subject_id)
                except ValueError:
                    raise ValidationError(
                        {"subject_id": "Invalid UUID format for subject ID."}
                    )
                queryset = queryset.filter(subject__id=subject_id)
            return queryset
        elif user.is_student:
            return Syllabus.objects.filter(
                institution__student_enrollments__user=user,
                curriculum_track__student_enrollments__user=user,
                section__student_enrollments__user=user,
                is_active=True,
            )
        elif user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if institution:
                queryset = Syllabus.objects.filter(
                    institution=institution, is_active=True
                )
                if subject_id:
                    try:
                        UUID(subject_id)
                    except ValueError:
                        raise ValidationError(
                            {"subject_id": "Invalid UUID format for subject ID."}
                        )
                    queryset = queryset.filter(subject__id=subject_id)
                return queryset
            return Syllabus.objects.none()
        else:
            memberships = InstitutionMembership.objects.filter(user=user)
            institution_ids = memberships.values_list("institution_id", flat=True)
            queryset = Syllabus.objects.filter(
                institution__id__in=institution_ids, is_active=True
            )
            if subject_id:
                try:
                    UUID(subject_id)
                except ValueError:
                    raise ValidationError(
                        {"subject_id": "Invalid UUID format for subject ID."}
                    )
                queryset = queryset.filter(subject__id=subject_id)
            return queryset

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
        if not institution:
            raise ValidationError({"institution_id": "Institution does not exist."})
        if not InstitutionMembership.objects.filter(
            user=user, institution=institution, role="teacher"
        ).exists():
            raise ValidationError(
                {"institution_id": "You are not enrolled in this institution."}
            )
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        if serializer.instance.created_by != user:
            return Response(
                {"error": "Only the creator can update this syllabus."},
                status=status.HTTP_403_FORBIDDEN,
            )
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
        if not institution:
            raise ValidationError({"institution_id": "Institution does not exist."})
        if not InstitutionMembership.objects.filter(
            user=user, institution=institution, role="teacher"
        ).exists():
            raise ValidationError(
                {"institution_id": "You are not enrolled in this institution."}
            )
        serializer.save()

    @action(
        detail=False,
        methods=["get"],
        url_path="by-subject/(?P<subject_id>[^/.]+)",
    )
    def by_subject(self, request, subject_id=None):
        user = request.user
        try:
            UUID(subject_id)
        except ValueError:
            raise ValidationError({"subject_id": "Invalid UUID format for subject ID."})

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject does not exist."},
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
            if not user.teacher_enrollments.filter(
                institution=institution,
                curriculum_track=subject.stream.curriculum_track,
                subjects=subject,
                is_active=True,
            ).exists():
                return Response(
                    {
                        "error": "You are not enrolled to teach this subject in this institution."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            queryset = Syllabus.objects.filter(
                institution=institution,
                subject=subject,
                is_active=True,
                curriculum_track__teacher_enrollments__user=user,
                section__teacher_enrollments__user=user,
                subject__teacher_enrollments__user=user,
            ).distinct()
        elif user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return Response(
                    {"error": "No institution found for this admin."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if subject.stream.curriculum_track.institution_info != institution:
                return Response(
                    {"error": "Subject does not belong to your institution."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            queryset = Syllabus.objects.filter(
                institution=institution, subject=subject, is_active=True
            )
        elif user.is_student:
            queryset = Syllabus.objects.filter(
                institution__student_enrollments__user=user,
                curriculum_track__student_enrollments__user=user,
                section__student_enrollments__user=user,
                subject=subject,
                is_active=True,
            )
        else:
            memberships = InstitutionMembership.objects.filter(user=user)
            institution_ids = memberships.values_list("institution_id", flat=True)
            queryset = Syllabus.objects.filter(
                institution__id__in=institution_ids, subject=subject, is_active=True
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
