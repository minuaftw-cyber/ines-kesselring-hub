from django.conf import settings
from rest_framework import serializers

from .models import DEMO_VIDEO_PREFIX as DEMO_PREFIX, Article, LiveStream, Series, Video


class VideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    youtube_url = serializers.CharField(read_only=True)
    is_demo = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id", "youtube_id", "title", "description", "thumbnail", "youtube_url",
            "published_at", "position", "is_demo", "series",
        )

    def get_is_demo(self, obj: Video) -> bool:
        return obj.youtube_id.startswith(DEMO_PREFIX)

    def get_thumbnail(self, obj: Video) -> str:
        return "" if self.get_is_demo(obj) else obj.display_thumbnail

    def get_series(self, obj: Video):
        if obj.series_id is None or not obj.series.is_published:
            return None
        return {"slug": obj.series.slug, "title": obj.series.title}


class SeriesSerializer(serializers.ModelSerializer):
    video_count = serializers.IntegerField(read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = ("id", "slug", "title", "description", "thumbnail", "video_count")

    def get_thumbnail(self, obj: Series) -> str:
        if obj.thumbnail_url:
            return obj.thumbnail_url
        first = next(
            (v for v in obj.videos.all() if v.is_published and not v.youtube_id.startswith(DEMO_PREFIX)),
            None,
        )
        return first.display_thumbnail if first else ""


class SeriesDetailSerializer(SeriesSerializer):
    videos = serializers.SerializerMethodField()

    class Meta(SeriesSerializer.Meta):
        fields = SeriesSerializer.Meta.fields + ("videos",)

    def get_videos(self, obj: Series):
        videos = sorted(
            (v for v in obj.videos.all() if v.is_published),
            key=lambda v: (v.position, v.published_at),
        )
        return VideoSerializer(videos, many=True, context=self.context).data


class LiveStreamSerializer(serializers.ModelSerializer):
    ends_at = serializers.DateTimeField(read_only=True)
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = LiveStream
        fields = (
            "id", "title", "description", "scheduled_at", "ends_at", "duration_minutes",
            "platform", "stream_url", "status", "is_members_only",
        )

    def get_stream_url(self, obj: LiveStream) -> str:
        request = self.context.get("request")
        signed_in = bool(request and request.user and request.user.is_authenticated)
        if obj.is_members_only and not signed_in:
            return ""
        return obj.stream_url


def media_url(file_field) -> str:
    if not file_field:
        return ""
    return f"{settings.MEDIA_PUBLIC_BASE_URL}{file_field.url}"


class ArticleListSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            "id", "slug", "title", "excerpt", "cover_image", "author_name",
            "is_members_only", "published_at",
        )

    def get_cover_image(self, obj: Article) -> str:
        return media_url(obj.cover_image)

    def get_author_name(self, obj: Article) -> str:
        if obj.author is None:
            return "Ines Kesselring"
        return obj.author.display_name or "Ines Kesselring"


class ArticleDetailSerializer(ArticleListSerializer):
    body = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ("body", "locked")

    def _is_locked(self, obj: Article) -> bool:
        request = self.context.get("request")
        signed_in = bool(request and request.user and request.user.is_authenticated)
        return obj.is_members_only and not signed_in

    def get_locked(self, obj: Article) -> bool:
        return self._is_locked(obj)

    def get_body(self, obj: Article) -> str:
        if self._is_locked(obj):
            # Members-only: show the first paragraph as a teaser.
            return obj.body.split("\n\n", 1)[0]
        return obj.body
