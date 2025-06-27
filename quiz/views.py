from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from .models import GlobalQuizQuestion, QuizContainer, QuizAttempt, QuizResponse
from .serializers import (
    GlobalQuizQuestionSerializer,
    QuizContainerSerializer,
    QuizAttemptSerializer,
    QuizSubmissionSerializer,
    ManualGradingSerializer,
    ParentQuizAttemptSerializer,
)
from institution.models import InstitutionInfo, StudentEnrollment, TeacherEnrollment
from user_management.models import ParentChildRelationship
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class QuizQuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = GlobalQuizQuestion.objects.all()
            global_module_id = request.query_params.get("global_module_id")
            global_unit_id = request.query_params.get("global_unit_id")
            global_lesson_id = request.query_params.get("global_lesson_id")
            global_micro_lesson_id = request.query_params.get("global_micro_lesson_id")
            if global_module_id:
                queryset = queryset.filter(module_id=global_module_id)
            if global_unit_id:
                queryset = queryset.filter(unit_id=global_unit_id)
            if global_lesson_id:
                queryset = queryset.filter(lesson_id=global_lesson_id)
            if global_micro_lesson_id:
                queryset = queryset.filter(micro_lesson_id=global_micro_lesson_id)
            serializer = GlobalQuizQuestionSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in QuizQuestionListCreateView.get: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            serializer = GlobalQuizQuestionSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Question created by user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Question creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in QuizQuestionListCreateView.post: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            question = get_object_or_404(GlobalQuizQuestion, pk=pk)
            serializer = GlobalQuizQuestionSerializer(question)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching question {pk}: {str(e)}")
            return Response(
                {"error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request, pk):
        try:
            question = get_object_or_404(GlobalQuizQuestion, pk=pk)
            if question.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to edit question {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = GlobalQuizQuestionSerializer(
                question, data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Question {pk} updated by user {request.user.id}")
                return Response(serializer.data)
            logger.error(f"Question update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating question {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            question = get_object_or_404(GlobalQuizQuestion, pk=pk)
            if question.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to delete question {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            question.delete()
            logger.info(f"Question {pk} deleted by user {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting question {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            institution = InstitutionInfo.objects.filter(
                memberships__user=user,
                memberships__role__in=["teacher", "student"],
            ).first()
            if not institution:
                logger.warning(f"User {user.id} not associated with any institution")
                return Response(
                    {"error": "User is not associated with an institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if user.is_teacher:
                queryset = QuizContainer.objects.filter(
                    created_by=user, curriculum_track__institution_info=institution
                )
            elif user.is_student:
                enrolled_tracks = StudentEnrollment.objects.filter(
                    user=user, institution=institution
                ).values_list("curriculum_track_id", flat=True)
                queryset = QuizContainer.objects.filter(
                    curriculum_track__id__in=enrolled_tracks,
                    curriculum_track__institution_info=institution,
                    is_active=True,
                    status="published",
                )
            else:
                queryset = QuizContainer.objects.none()
            serializer = QuizContainerSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in QuizListCreateView.get: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            if not request.user.is_teacher:
                logger.warning(
                    f"Non-teacher user {request.user.id} attempted to create quiz"
                )
                return Response(
                    {"error": "Only teachers can create quizzes"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = QuizContainerSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                quiz = serializer.save()
                logger.info(f"Quiz {quiz.id} created by user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Quiz creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(
                f"Database integrity error in QuizListCreateView.post: {str(e)}"
            )
            return Response(
                {"error": f"Database error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error in QuizListCreateView.post: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed quiz {pk} from another institution"
                )
                return Response(
                    {"error": "Quiz does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = QuizContainerSerializer(quiz)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            if quiz.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to edit quiz {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(f"Quiz {pk} not in user {request.user.id}'s institution")
                return Response(
                    {"error": "Quiz does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = QuizContainerSerializer(
                quiz, data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Quiz {pk} updated by user {request.user.id}")
                return Response(serializer.data)
            logger.error(f"Quiz update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            if quiz.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized to delete quiz {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(f"Quiz {pk} not in user {request.user.id}'s institution")
                return Response(
                    {"error": "Quiz does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            quiz.delete()
            logger.info(f"Quiz {pk} deleted by user {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed quiz {pk} from another institution"
                )
                return Response(
                    {"error": "Quiz does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            questions = quiz.questions.all()
            serializer = GlobalQuizQuestionSerializer(questions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching questions for quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed quiz {pk} from another institution"
                )
                return Response(
                    {"error": "Quiz does not belong to your institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not quiz.is_active or quiz.status != "published":
                logger.warning(f"Quiz {pk} is not available for user {request.user.id}")
                return Response(
                    {"error": "Quiz is not available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not request.user.is_student:
                logger.warning(
                    f"Non-student user {request.user.id} attempted to start quiz {pk}"
                )
                return Response(
                    {"error": "Only students can attempt quizzes"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not StudentEnrollment.objects.filter(
                user=request.user,
                curriculum_track=quiz.curriculum_track,
                institution=institution,
                is_active=True,
            ).exists():
                logger.warning(
                    f"User {request.user.id} not enrolled in curriculum track for quiz {pk}"
                )
                return Response(
                    {"error": "You are not enrolled in this curriculum track"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            attempt, created = QuizAttempt.objects.get_or_create(
                quiz=quiz,
                user=request.user,
                status="started",
                defaults={"started_at": timezone.now()},
            )
            serializer = QuizAttemptSerializer(attempt)
            logger.info(
                f"Quiz attempt {'created' if created else 'retrieved'} for quiz {pk} by user {request.user.id}"
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error starting quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if quiz.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} attempted to submit quiz {pk} from another institution"
                )
                return Response(
                    {"error": "Quiz does not exist in your institution"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = QuizSubmissionSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                result = serializer.save()
                logger.info(f"Quiz {pk} submitted by user {request.user.id}")
                return Response(result, status=status.HTTP_201_CREATED)
            logger.error(f"Quiz submission failed for quiz {pk}: {serializer.errors}")
            return Response(
                serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            logger.error(f"Error submitting quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizGradeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = get_object_or_404(QuizContainer, pk=pk)
            serializer = ManualGradingSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Quiz {pk} graded by user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Quiz grading failed for quiz {pk}: {serializer.errors}")
            return Response(
                serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            logger.error(f"Error grading quiz {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizAttemptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            institution = InstitutionInfo.objects.filter(memberships__user=user).first()
            if not institution:
                logger.warning(f"User {user.id} not associated with any institution")
                return Response(
                    {"error": "Institution not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user.is_teacher:
                queryset = QuizAttempt.objects.filter(
                    quiz__created_by=user,
                    quiz__curriculum_track__institution_info=institution,
                )
            elif user.is_student:
                queryset = QuizAttempt.objects.filter(
                    user=user,
                    quiz__curriculum_track__institution_info=institution,
                )
            else:
                queryset = QuizAttempt.objects.none()
            serializer = QuizAttemptSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching quiz attempts: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuizAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            attempt = get_object_or_404(QuizAttempt, pk=pk)
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if attempt.quiz.curriculum_track.institution_info != institution:
                logger.warning(
                    f"User {request.user.id} accessed attempt {pk} from another institution"
                )
                return Response(
                    {"error": "Attempt does not belong to your institution"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if attempt.user != request.user and attempt.quiz.created_by != request.user:
                logger.warning(
                    f"User {request.user.id} not authorized for attempt {pk}"
                )
                return Response(
                    {"error": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = QuizAttemptSerializer(attempt)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching attempt {pk}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParentQuizAttemptListView(APIView):
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
            if not user.is_parent:
                logger.warning(f"Non-parent user {user.id} accessed parent attempts")
                return Response(
                    {"error": "Only parents can access this endpoint"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            children_ids = ParentChildRelationship.objects.filter(
                parent=user, institution=institution
            ).values_list("child_id", flat=True)
            if not children_ids:
                return Response([])
            queryset = QuizAttempt.objects.filter(
                user__id__in=children_ids,
                quiz__curriculum_track__institution_info=institution,
            )
            serializer = ParentQuizAttemptSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching parent quiz attempts: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
