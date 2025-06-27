from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_management.serializers.user_info import UserInfoSerializer


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user role information",
        operation_description="""
        Retrieves the role-related information for the authenticated user, including whether they are a teacher,
        student, institution admin, parent, or admission seeker.
        """,
        responses={
            200: openapi.Response(
                description="User role information retrieved successfully",
                schema=UserInfoSerializer(),
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def get(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
