from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Exam, ExamMark
from .serializers import ExamSerializer, ExamMarkSerializer
from institution.models import InstitutionInfo, StudentEnrollment, TeacherEnrollment
import logging

logger = logging.getLogger(__name__)


class ExamListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            institution = InstitutionInfo.objects.filter(memberships__user=user).first()
            if not institution:
                logger.warning(f"User {user.id} not associated with any institution")
                return Response(
                    {"error": "User is not associated with an institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            queryset = Exam.objects.filter(
                curriculum_track__institution_info=institution, is_active=True
            )

            # Apply filters
            section_id = request.query_params.get("section_id")
            subject_id = request.query_params.get("subject_id")

            if section_id:
                queryset = queryset.filter(section__id=section_id)
            if subject_id:
                queryset = queryset.filter(subject__id=subject_id)

            if user.is_teacher:
                # Teachers see only exams they created or are enrolled to teach
                queryset = queryset.filter(created_by=user) | queryset.filter(
                    section__teacher_enrollments__user=user,
                    subject__teacher_enrollments__user=user,
                )
            elif user.is_student:
                # Students see only exams in their enrolled sections
                enrolled_sections = StudentEnrollment.objects.filter(
                    user=user, is_active=True
                ).values_list("section__id", flat=True)
                queryset = queryset.filter(section__id__in=enrolled_sections)
            else:
                logger.warning(f"User {user.id} has invalid role")
                return Response(
                    {"error": "Invalid user role"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ExamSerializer(queryset.distinct(), many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching exams: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            if not request.user.is_teacher:
                logger.warning(
                    f"Non-teacher user {request.user.id} attempted to create exam"
                )
                return Response(
                    {"error": "Only teachers can create exams"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ExamSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                exam = serializer.save()
                logger.info(f"Exam {exam.id} created by user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Exam creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating exam: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            exam = get_object_or_404(Exam, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if exam.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed exam {pk} from another institution"
                )
                return Response(
                    {"error": "Exam does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if request.user.is_student:
                # Students can only see exams in their enrolled sections
                if not StudentEnrollment.objects.filter(
                    user=request.user, section=exam.section, is_active=True
                ).exists():
                    logger.warning(
                        f"Student {request.user.id} not enrolled in section {exam.section.id}"
                    )
                    return Response(
                        {"error": "You are not enrolled in this exam's section"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            serializer = ExamSerializer(exam)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching exam {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            exam = get_object_or_404(Exam, pk=pk)
            if exam.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to edit exam {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ExamSerializer(
                exam, data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Exam {pk} updated by user {request.user.id}")
                return Response(serializer.data)
            logger.error(f"Exam update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating exam {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            exam = get_object_or_404(Exam, pk=pk)
            if exam.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to delete exam {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            exam.is_active = False
            exam.save()
            logger.info(f"Exam {pk} deleted by user {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting exam {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExamMarkListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if not user.is_teacher:
                logger.warning(
                    f"Non-teacher user {user.id} attempted to access exam marks"
                )
                return Response(
                    {"error": "Only teachers can view exam marks"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            institution = InstitutionInfo.objects.filter(
                memberships__user=user,
                memberships__role="teacher",
            ).first()
            if not institution:
                logger.warning(f"User {user.id} not associated with any institution")
                return Response(
                    {"error": "User is not associated with an institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            queryset = ExamMark.objects.filter(
                exam__curriculum_track__institution_info=institution,
                exam__section__teacher_enrollments__user=user,
                exam__subject__teacher_enrollments__user=user,
            )

            # Apply filters
            exam_id = request.query_params.get("exam_id")
            section_id = request.query_params.get("section_id")
            subject_id = request.query_params.get("subject_id")

            if exam_id:
                queryset = queryset.filter(exam__id=exam_id)
            if section_id:
                queryset = queryset.filter(exam__section__id=section_id)
            if subject_id:
                queryset = queryset.filter(exam__subject__id=subject_id)

            serializer = ExamMarkSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching exam marks: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            if not request.user.is_teacher:
                logger.warning(
                    f"Non-teacher user {request.user.id} attempted to create exam mark"
                )
                return Response(
                    {"error": "Only teachers can assign exam marks"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ExamMarkSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                mark = serializer.save()
                logger.info(f"Exam mark {mark.id} created by user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Exam mark creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating exam mark: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExamMarkDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            mark = get_object_or_404(ExamMark, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if mark.exam.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed exam mark {pk} from another institution"
                )
                return Response(
                    {"error": "Exam mark does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if mark.exam.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized for exam mark {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ExamMarkSerializer(mark)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching exam mark {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            mark = get_object_or_404(ExamMark, pk=pk)
            if mark.exam.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to edit exam mark {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ExamMarkSerializer(
                mark, data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Exam mark {pk} updated by user {request.user.id}")
                return Response(serializer.data)
            logger.error(f"Exam mark update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating exam mark {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            mark = get_object_or_404(ExamMark, pk=pk)
            if mark.exam.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to delete exam mark {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            mark.delete()
            logger.info(f"Exam mark {pk} deleted by user {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting exam mark {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
