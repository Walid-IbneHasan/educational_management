# user_management/permissions/authentication.py
from rest_framework import permissions
from institution.models import InstitutionInfo


class IsInstitutionAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        print(
            f"User: {request.user}, is_authenticated: {request.user.is_authenticated}, is_institution: {request.user.is_institution}"
        )  # Debug
        return request.user.is_authenticated and request.user.is_institution

    def has_object_permission(self, request, view, obj):
        print(
            f"Object type: {type(obj)}, User: {request.user}, is_institution: {request.user.is_institution}"
        )  # Debug
        if isinstance(obj, InstitutionInfo):
            return obj.admin == request.user
        return False


class IsInstitutionMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.memberships.exists()


class IsTeacherForQuizCreation(permissions.BasePermission):
    """
    Permission class to allow only users with is_teacher=True to create quizzes.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher


class IsStudentForQuizParticipation(permissions.BasePermission):
    """
    Permission class to allow only users with is_student=True to participate in quizzes.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student


class IsInstitutionOrTeacher(permissions.BasePermission):
    """
    Permission class to allow both for institution and is_teacher.
    """

    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # Allow POST, PUT, DELETE only for institution or teacher
        return request.user.is_authenticated and (
            getattr(request.user, "institution", False)
            or getattr(request.user, "is_teacher", False)
        )


from rest_framework import permissions


class IsInstitutionAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_institution
        )


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_teacher
        )


class IsQuizCreatorForGrading(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_teacher or request.user.is_institution
        )
