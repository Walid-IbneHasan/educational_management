from django.urls import path
from notice.views import NoticeViewSet

app_name = "notice"

urlpatterns = [
    path(
        "",
        NoticeViewSet.as_view({"get": "list", "post": "create"}),
        name="notice-list",
    ),
    path(
        "<uuid:pk>/",
        NoticeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="notice-detail",
    ),
]
