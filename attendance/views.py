from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from attendance.models import Attendance
from attendance.serializers import (
    AttendanceSerializer,
    AttendanceStatisticsSerializer,
    BulkAttendanceSerializer,
    StudentAttendanceSerializer,
)
from user_management.models.authentication import (
    InstitutionMembership,
    ParentChildRelationship,
)
from institution.models import InstitutionInfo
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Q
import logging

logger = logging.getLogger("attendance")


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Filter by institution
        institution_ids = InstitutionMembership.objects.filter(user=user).values_list(
            "institution_id", flat=True
        )
        queryset = queryset.filter(institution__in=institution_ids)

        # Role-based filtering
        if user.is_teacher:
            # Teachers see attendance for their enrolled sections and subjects
            enrolled_sections = user.teacher_enrollments.filter(
                is_active=True
            ).values_list(
                "section__id", flat=True
            )  # Changed from section_id to section__id
            enrolled_subjects = user.teacher_enrollments.filter(
                is_active=True
            ).values_list("subjects__id", flat=True)
            queryset = queryset.filter(
                section__id__in=enrolled_sections, subject__id__in=enrolled_subjects
            )
        elif user.is_student:
            # Students see only their own attendance
            queryset = queryset.filter(student=user)
        elif user.is_parents:
            # Parents see attendance of their children
            child_ids = ParentChildRelationship.objects.filter(parent=user).values_list(
                "child_id", flat=True
            )
            queryset = queryset.filter(student__id__in=child_ids)
        else:
            # Non-teachers, non-students, non-parents see nothing
            queryset = queryset.none()

        # Apply filters from query params
        date = self.request.query_params.get("date")
        section_id = self.request.query_params.get("section_id")
        subject_id = self.request.query_params.get("subject_id")
        student_id = self.request.query_params.get("student_id")

        if date:
            try:
                queryset = queryset.filter(date=date)
            except ValueError:
                raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD."})
        if section_id:
            queryset = queryset.filter(section__id=section_id)
        if subject_id:
            queryset = queryset.filter(subject__id=subject_id)
        if student_id and (user.is_teacher or user.is_parents):
            queryset = queryset.filter(student__id=student_id)

        return queryset.order_by("-date")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"] and (
            self.request.user.is_student or self.request.user.is_parents
        ):
            return StudentAttendanceSerializer
        elif self.action == "bulk_create":
            return BulkAttendanceSerializer
        return AttendanceSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # Only allow updates by the teacher who created it or teachers of the same section/subject
        instance = self.get_object()
        if instance.created_by != self.request.user:
            if not self.request.user.teacher_enrollments.filter(
                section=instance.section, subjects=instance.subject, is_active=True
            ).exists():
                raise ValidationError(
                    "You are not authorized to update this attendance."
                )
        serializer.save()

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request):
        serializer = BulkAttendanceSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    attendances = []
                    for att in serializer.validated_data["attendances"]:
                        attendance = Attendance(
                            institution=serializer.validated_data["institution"],
                            student_id=att["student_id"],
                            section=serializer.validated_data["section"],
                            subject=serializer.validated_data["subject"],
                            date=serializer.validated_data["date"],
                            status=att["status"],
                            created_by=request.user,
                        )
                        attendance.clean()
                        attendances.append(attendance)
                    Attendance.objects.bulk_create(attendances, ignore_conflicts=False)
                logger.info(f"Bulk attendance created by user {request.user.id}")
                return Response(
                    {"message": "Bulk attendance recorded successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Bulk attendance creation error: {str(e)}")
                raise ValidationError(str(e))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        user = request.user
        queryset = Attendance.objects.all()

        # Filter by institution
        institution_ids = InstitutionMembership.objects.filter(user=user).values_list(
            "institution_id", flat=True
        )
        queryset = queryset.filter(institution__in=institution_ids)

        # Role-based filtering
        if user.is_teacher:
            enrolled_sections = user.teacher_enrollments.filter(
                is_active=True
            ).values_list("section__id", flat=True)
            enrolled_subjects = user.teacher_enrollments.filter(
                is_active=True
            ).values_list("subjects__id", flat=True)
            queryset = queryset.filter(
                section__id__in=enrolled_sections, subject__id__in=enrolled_subjects
            )
        elif user.is_student:
            queryset = queryset.filter(student=user)
        else:
            return Response(
                {"detail": "You are not authorized to view attendance statistics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Apply filters from query params
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        section_id = request.query_params.get("section_id")
        subject_id = request.query_params.get("subject_id")
        student_id = request.query_params.get("student_id")

        if start_date:
            try:
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                raise ValidationError({"start_date": "Invalid date format. Use YYYY-MM-DD."})
        if end_date:
            try:
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                raise ValidationError({"end_date": "Invalid date format. Use YYYY-MM-DD."})
        if section_id:
            queryset = queryset.filter(section__id=section_id)
        if subject_id:
            queryset = queryset.filter(subject__id=subject_id)
        if student_id and user.is_teacher:
            queryset = queryset.filter(student__id=student_id)

        # Aggregate statistics
        stats = (
            queryset.values(
                "student__id",
                "student__first_name",
                "section__name",
                "subject__name",
            )
            .annotate(
                present_count=Count("id", filter=Q(status="present")),
                absent_count=Count("id", filter=Q(status="absent")),
                late_count=Count("id", filter=Q(status="late")),
                excused_count=Count("id", filter=Q(status="excused")),
            )
            .order_by("student__first_name")
        )

        serializer = AttendanceStatisticsSerializer(stats, many=True)
        return Response(serializer.data)