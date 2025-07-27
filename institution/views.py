from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from user_management.permissions.authentication import IsInstitutionAdmin, IsTeacher
from .models import *
from .serializers import *
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from uuid import UUID
from rest_framework.decorators import action


class InstitutionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if view.__class__.__name__ == "ClassViewSet" and request.method == "POST":
            return request.user.is_authenticated and request.user.is_institution
        return request.user.is_authenticated and (
            request.user.is_institution or request.user.is_teacher
        )


class InstitutionInfoViewSet(viewsets.ModelViewSet):
    queryset = InstitutionInfo.objects.all()
    serializer_class = InstitutionInfoSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]

    def get_queryset(self):
        return InstitutionInfo.objects.filter(admin=self.request.user)


class MyInstitutionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = InstitutionInfo.objects.filter(admin=request.user).first()
        if not institution:
            return Response(
                {"error": "No institution found for this user"},
                status=status.HTTP_200_OK,
            )
        serializer = InstitutionInfoSerializer(institution)
        return Response(serializer.data)


class GlobalCurriculumTrackViewSet(viewsets.ModelViewSet):
    queryset = GlobalCurriculumTrack.objects.all()
    serializer_class = GlobalCurriculumTrackSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalStreamViewSet(viewsets.ModelViewSet):
    queryset = GlobalStream.objects.all()
    serializer_class = GlobalStreamSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalSubjectViewSet(viewsets.ModelViewSet):
    queryset = GlobalSubject.objects.all()
    serializer_class = GlobalSubjectSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalModuleViewSet(viewsets.ModelViewSet):
    queryset = GlobalModule.objects.all()
    serializer_class = GlobalModuleSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalUnitViewSet(viewsets.ModelViewSet):
    queryset = GlobalUnit.objects.all()
    serializer_class = GlobalUnitSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalLessonViewSet(viewsets.ModelViewSet):
    queryset = GlobalLesson.objects.all()
    serializer_class = GlobalLessonSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class GlobalMicroLessonViewSet(viewsets.ModelViewSet):
    queryset = GlobalMicroLesson.objects.all()
    serializer_class = GlobalMicroLessonSerializer
    permission_classes = [IsAuthenticated, InstitutionPermission]


class CurriculumTrackViewSet(viewsets.ModelViewSet):
    serializer_class = CurriculumTrackSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return CurriculumTrack.objects.none()
        return CurriculumTrack.objects.filter(institution_info=institution)

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
        serializer.save(institution_info=institution)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return Section.objects.none()
        return Section.objects.filter(curriculum_track__institution_info=institution)

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
        serializer.save()


class StreamViewSet(viewsets.ModelViewSet):
    serializer_class = StreamSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return Stream.objects.none()
        return Stream.objects.filter(curriculum_track__institution_info=institution)

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
        serializer.save()


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return Subject.objects.none()
        queryset = Subject.objects.filter(
            stream__curriculum_track__institution_info=institution
        )
        stream_id = self.request.query_params.get("streams")
        if stream_id:
            try:
                UUID(stream_id)  # Validate UUID format
                if not Stream.objects.filter(
                    id=stream_id, curriculum_track__institution_info=institution
                ).exists():
                    raise ValidationError(
                        f"Stream with ID {stream_id} does not exist or does not belong to this institution."
                    )
                queryset = queryset.filter(stream__id=stream_id)
            except ValueError:
                raise ValidationError(f"Invalid UUID format for stream ID: {stream_id}")
        return queryset

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
        serializer.save()


class ModuleViewSet(viewsets.ModelViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin | IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return Module.objects.none()
            return Module.objects.filter(
                subject__stream__curriculum_track__institution_info=institution
            )
        elif user.is_teacher:
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
                return Module.objects.filter(
                    subject__teacher_enrollments__user=user,
                    subject__teacher_enrollments__is_active=True,
                    subject__stream__curriculum_track__institution_info__id=institution_id,
                    is_active=True,
                ).distinct()
            return Module.objects.filter(
                subject__teacher_enrollments__user=user,
                subject__teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Module.objects.none()

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
            subject = serializer.validated_data["subject"]
            if not TeacherEnrollment.objects.filter(
                user=user, subjects=subject, is_active=True
            ).exists():
                raise ValidationError("You are not enrolled to teach this subject.")
            if subject.stream.curriculum_track.institution_info != institution:
                raise ValidationError(
                    "Subject does not belong to the specified institution."
                )
            serializer.save()


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin | IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return Unit.objects.none()
            return Unit.objects.filter(
                module__subject__stream__curriculum_track__institution_info=institution
            )
        elif user.is_teacher:
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
                return Unit.objects.filter(
                    module__subject__teacher_enrollments__user=user,
                    module__subject__teacher_enrollments__is_active=True,
                    module__subject__stream__curriculum_track__institution_info__id=institution_id,
                    is_active=True,
                ).distinct()
            return Unit.objects.filter(
                module__subject__teacher_enrollments__user=user,
                module__subject__teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Unit.objects.none()

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
            module = serializer.validated_data["module"]
            if not TeacherEnrollment.objects.filter(
                user=user, subjects=module.subject, is_active=True
            ).exists():
                raise ValidationError("You are not enrolled to teach this subject.")
            if module.subject.stream_curriculum_track.institution_info != institution:
                raise ValidationError(
                    "Module does not belong to the specified institution."
                )
            serializer.save()


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin | IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return Lesson.objects.none()
            return Lesson.objects.filter(
                unit__module__subject__stream__curriculum_track__institution_info=institution
            )
        elif user.is_teacher:
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
                return Lesson.objects.filter(
                    unit__module__subject__teacher_enrollments__user=user,
                    unit__module__subject__teacher_enrollments__is_active=True,
                    unit__module__subject__stream__curriculum_track__institution_info__id=institution_id,
                    is_active=True,
                ).distinct()
            return Lesson.objects.filter(
                unit__module__subject__teacher_enrollments__user=user,
                unit__module__subject__teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Lesson.objects.none()

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
            unit = serializer.validated_data["unit"]
            if not TeacherEnrollment.objects.filter(
                user=user, subjects=unit.module.subject, is_active=True
            ).exists():
                raise ValidationError("You are not enrolled to teach this subject.")
            if (
                unit.module.subject.stream.curriculum_track.institution_info
                != institution
            ):
                raise ValidationError(
                    "Unit does not belong to the specified institution."
                )
            serializer.save()


class MicroLessonViewSet(viewsets.ModelViewSet):
    serializer_class = MicroLessonSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin | IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_institution:
            institution = InstitutionInfo.objects.filter(admin=user).first()
            if not institution:
                return MicroLesson.objects.none()
            return MicroLesson.objects.filter(
                lesson__unit__module__subject__stream__curriculum_track__institution_info=institution
            )
        elif user.is_teacher:
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
                return MicroLesson.objects.filter(
                    lesson__unit__module__subject__teacher_enrollments__user=user,
                    lesson__unit__module__subject__teacher_enrollments__is_active=True,
                    lesson__unit__module__subject__stream__curriculum_track__institution_info__id=institution_id,
                    is_active=True,
                ).distinct()
            return MicroLesson.objects.filter(
                lesson__unit__module__subject__teacher_enrollments__user=user,
                lesson__unit__module__subject__teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return MicroLesson.objects.none()

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
            lesson = serializer.validated_data["lesson"]
            if not TeacherEnrollment.objects.filter(
                user=user, subjects=lesson.unit.module.subject, is_active=True
            ).exists():
                raise ValidationError("You are not enrolled to teach this subject.")
            if (
                lesson.unit.module.subject.stream.curriculum_track.institution_info
                != institution
            ):
                raise ValidationError(
                    "Lesson does not belong to the specified institution."
                )
            serializer.save()


class TeacherEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherEnrollmentSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return TeacherEnrollment.objects.none()
        return TeacherEnrollment.objects.filter(institution=institution)

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


class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return StudentEnrollment.objects.none()
        return StudentEnrollment.objects.filter(institution=institution)

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

    def get_permissions(self):
        if self.action == "by_section":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="by-section")
    def by_section(self, request):
        user = request.user
        section_id = request.query_params.get("section_id")

        if not section_id:
            raise ValidationError({"section_id": "Section ID is required."})
        try:
            UUID(section_id)
        except ValueError:
            raise ValidationError({"section_id": "Invalid UUID format for section ID."})

        # Check if user is institution admin or teacher enrolled in the section
        institution = InstitutionInfo.objects.filter(admin=user).first()
        if not (
            (user.is_institution and institution)
            or (
                user.is_teacher
                and TeacherEnrollment.objects.filter(
                    user=user, section__id=section_id, is_active=True
                ).exists()
            )
        ):
            return Response(
                {"detail": "You are not authorized to access this section."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get student enrollments for the section
        queryset = StudentEnrollment.objects.filter(
            section__id=section_id,
            is_active=True,
        )
        if user.is_institution and institution:
            queryset = queryset.filter(institution=institution)
        elif user.is_teacher:
            queryset = queryset.filter(
                institution__in=InstitutionMembership.objects.filter(user=user).values(
                    "institution"
                )
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# TO GET THE CURRICULUM TRACKS, SECTIONS AND SUBJECTS FOR THE LOGGED IN USER


class MyCurriculumTrackViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CurriculumTrackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return CurriculumTrack.objects.filter(
                teacher_enrollments__user=user,
                teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        elif user.is_student:
            return CurriculumTrack.objects.filter(
                student_enrollments__user=user,
                student_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return CurriculumTrack.objects.none()


class MySectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Section.objects.filter(
                teacher_enrollments__user=user,
                teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        elif user.is_student:
            return Section.objects.filter(
                student_enrollments__user=user,
                student_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Section.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class MySubjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Subject.objects.filter(
                teacher_enrollments__user=user,
                teacher_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        elif user.is_student:
            # Students get subjects via their enrolled section's stream
            return Subject.objects.filter(
                stream__section__student_enrollments__user=user,
                stream__section__student_enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Subject.objects.none()


class MySubjectByInstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        institution_id = self.request.query_params.get("institution_id")

        if not institution_id:
            raise ValidationError({"institution_id": "Institution ID is required."})
        try:
            UUID(institution_id)
        except ValueError:
            raise ValidationError(
                {"institution_id": "Invalid UUID format for institution ID."}
            )

        if user.is_teacher:
            return Subject.objects.filter(
                teacher_enrollments__user=user,
                teacher_enrollments__is_active=True,
                is_active=True,
                stream__curriculum_track__institution_info__id=institution_id,
            ).distinct()
        elif user.is_student:
            return Subject.objects.filter(
                stream__section__student_enrollments__user=user,
                stream__section__student_enrollments__is_active=True,
                is_active=True,
                stream__curriculum_track__institution_info__id=institution_id,
            ).distinct()
        return Subject.objects.none()


# ............................#
#    PAYMENT FEES VIEW SET
# ............................#


from .serializers import (
    InstitutionFeeSerializer,
    CurriculumTrackFeeSerializer,
    StudentFeeSerializer,
)
from .models import InstitutionFee, CurriculumTrackFee, StudentFee


class InstitutionFeeViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionFeeSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return InstitutionFee.objects.none()
        return InstitutionFee.objects.filter(institution=institution)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if institution:
            context["institution"] = institution
        return context


class CurriculumTrackFeeViewSet(viewsets.ModelViewSet):
    serializer_class = CurriculumTrackFeeSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return CurriculumTrackFee.objects.none()
        return CurriculumTrackFee.objects.filter(
            curriculum_track__institution_info=institution
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if institution:
            context["institution"] = institution
        return context


class StudentFeeViewSet(viewsets.ModelViewSet):
    serializer_class = StudentFeeSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get_queryset(self):
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if not institution:
            return StudentFee.objects.none()
        return StudentFee.objects.filter(student_enrollment__institution=institution)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        institution = InstitutionInfo.objects.filter(admin=self.request.user).first()
        if institution:
            context["institution"] = institution
        return context
