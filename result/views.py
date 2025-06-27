from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import StudentResultSerializer, SectionResultSerializer
from institution.models import InstitutionInfo
import logging

logger = logging.getLogger(__name__)


class StudentResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            institution = InstitutionInfo.objects.filter(
                memberships__user=request.user
            ).first()
            if not institution:
                logger.warning(
                    f"User {request.user.id} not associated with any institution"
                )
                return Response(
                    {"error": "User is not associated with an institution"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = StudentResultSerializer(
                data={"student_id": student_id}, context={"request": request}
            )
            if serializer.is_valid():
                return Response(serializer.data)
            logger.error(f"Result retrieval failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching results for student {student_id}: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SectionResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            section_id = request.query_params.get("section_id")
            subject_id = request.query_params.get("subject_id")
            student_id = request.query_params.get("student_id")

            logger.debug(
                f"Section result query: section_id={section_id}, subject_id={subject_id}, student_id={student_id}"
            )

            if not section_id:
                logger.error("Section ID is required")
                return Response(
                    {"error": "Section ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SectionResultSerializer(
                data={
                    "section_id": section_id,
                    "subject_id": subject_id or None,
                    "student_id": student_id or None,
                },
                context={"request": request},
            )
            if serializer.is_valid():
                logger.debug(
                    f"Section result serialized successfully for section {section_id}"
                )
                return Response(serializer.data)
            logger.error(f"Section result retrieval failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching section results: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
