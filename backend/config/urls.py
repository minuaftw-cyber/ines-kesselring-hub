from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Ines Kesselring Backoffice"
admin.site.site_title = "Ines Kesselring Backoffice"
admin.site.index_title = "Manage videos, live schedule, news and members"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("content.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
