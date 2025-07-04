from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from educational_management.swagger import schema_view
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    return HttpResponse("OK", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check), #For docker compose and nginx health check
    path("auth/", include("user_management.urls.authentication")),
    path("auth/", include("user_management.urls.admission_seeker")),
    path("bkash/", include("payment_management.urls.bkash")),
    path("bkash/fees/", include("payment_management.urls.fees")),
    path("scholarship/", include("scholarship.urls")),
    path("institution/", include("institution.urls")),
    path("attendance/", include("attendance.urls")),
    path("quiz/", include("quiz.urls")),
    path("notice/", include("notice.urls")),
    path("syllabus/", include("syllabus.urls")),
    path("homework/", include("homework.urls")),
    path("exam/", include("exam.urls")),
    path("result/", include("result.urls")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
