import logging
from datetime import timedelta

from django.db import connection
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Article, LiveStream, Series, Video
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    LiveStreamSerializer,
    SeriesDetailSerializer,
    SeriesSerializer,
    VideoSerializer,
)

logger = logging.getLogger(__name__)


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        return (
            Series.objects.published()
            .annotate(video_count=Count("videos", filter=Q(videos__is_published=True)))
            # Aggregation queries ignore Meta.ordering, so order explicitly.
            .order_by("sort_order", "-created_at")
            .prefetch_related(Prefetch("videos", queryset=Video.objects.order_by("position", "published_at")))
        )

    def get_serializer_class(self):
        return SeriesDetailSerializer if self.action == "retrieve" else SeriesSerializer


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Latest videos first. Optional ?series=<slug>."""

    serializer_class = VideoSerializer
    lookup_field = "youtube_id"

    def get_queryset(self):
        queryset = Video.objects.published().select_related("series")
        series = self.request.query_params.get("series")
        if series:
            queryset = queryset.filter(series__slug=series)
        return queryset


class ScheduleView(generics.ListAPIView):
    """Upcoming (and currently live) streams. ?past=1 returns recent past streams."""

    serializer_class = LiveStreamSerializer
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        queryset = LiveStream.objects.published()
        if self.request.query_params.get("past"):
            return queryset.filter(scheduled_at__lt=now).order_by("-scheduled_at")[:20]
        # Keep a stream visible while it may still be running.
        return queryset.filter(
            Q(status=LiveStream.Status.LIVE)
            | Q(status=LiveStream.Status.SCHEDULED, scheduled_at__gte=now - timedelta(hours=6))
        ).order_by("scheduled_at")


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"

    def get_queryset(self):
        return Article.objects.published().filter(published_at__lte=timezone.now()).select_related("author")

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Liveness + database check, for uptime monitors and Docker healthchecks."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        database = "ok"
    except Exception:  # noqa: BLE001 - report any database failure
        logger.exception("Health check: database unavailable")
        return Response({"status": "error", "database": "unavailable"}, status=503)
    return Response({"status": "ok", "database": database, "time": timezone.now()})
