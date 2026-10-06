from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from .models import DEMO_VIDEO_PREFIX, Article, LiveStream, Series, Video
from .youtube import YouTubeSyncError, sync_channel


def thumb(url: str, width: int = 96):
    if not url:
        return format_html('<span style="color:#999">—</span>')
    return format_html(
        '<img src="{}" width="{}" style="aspect-ratio:16/9;object-fit:cover;border-radius:4px" loading="lazy">',
        url, width,
    )


@admin.action(description="Publish selected")
def make_published(modeladmin, request, queryset):
    updated = queryset.update(is_published=True)
    modeladmin.message_user(request, f"Published {updated} item(s).", messages.SUCCESS)


@admin.action(description="Unpublish selected")
def make_unpublished(modeladmin, request, queryset):
    updated = queryset.update(is_published=False)
    modeladmin.message_user(request, f"Unpublished {updated} item(s).", messages.SUCCESS)


class VideoInline(admin.TabularInline):
    model = Video
    fields = ("preview", "title", "youtube_id", "position", "published_at", "is_published")
    readonly_fields = ("preview",)
    extra = 0
    ordering = ("position", "published_at")
    show_change_link = True

    @admin.display(description="")
    def preview(self, obj: Video):
        if obj.pk is None or obj.youtube_id.startswith(DEMO_VIDEO_PREFIX):
            return thumb("")
        return thumb(obj.display_thumbnail, 80)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "video_total", "sort_order", "is_published", "youtube_playlist_id", "updated_at")
    list_display_links = ("preview", "title")
    list_editable = ("sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "description", "youtube_playlist_id")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [VideoInline]
    actions = [make_published, make_unpublished, "sync_from_youtube"]

    @admin.display(description="")
    def preview(self, obj: Series):
        if obj.thumbnail_url:
            return thumb(obj.thumbnail_url)
        first = obj.videos.exclude(youtube_id__startswith=DEMO_VIDEO_PREFIX).first()
        return thumb(first.display_thumbnail if first else "")

    @admin.display(description="Videos")
    def video_total(self, obj: Series) -> int:
        return obj.videos.count()

    @admin.action(description="Sync selected series from YouTube")
    def sync_from_youtube(self, request, queryset):
        playlist_ids = list(queryset.exclude(youtube_playlist_id=None).values_list("youtube_playlist_id", flat=True))
        if not playlist_ids:
            self.message_user(request, "None of the selected series are linked to a YouTube playlist.", messages.WARNING)
            return
        try:
            result = sync_channel(playlist_ids=playlist_ids)
        except YouTubeSyncError as exc:
            self.message_user(request, f"YouTube sync failed: {exc}", messages.ERROR)
            return
        self.message_user(request, result.summary(), messages.SUCCESS)
        for error in result.errors:
            self.message_user(request, error, messages.WARNING)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "series", "published_at", "is_published", "watch_link")
    list_display_links = ("preview", "title")
    list_editable = ("is_published",)
    list_filter = ("is_published", "series")
    search_fields = ("title", "description", "youtube_id")
    date_hierarchy = "published_at"
    autocomplete_fields = ("series",)
    readonly_fields = ("large_preview", "created_at", "updated_at")
    actions = [make_published, make_unpublished]
    fieldsets = (
        (None, {"fields": ("large_preview", "title", "youtube_id", "series", "position")}),
        ("Details", {"fields": ("description", "thumbnail_url", "published_at", "is_published")}),
        ("History", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="")
    def preview(self, obj: Video):
        if obj.youtube_id.startswith(DEMO_VIDEO_PREFIX):
            return thumb("")
        return thumb(obj.display_thumbnail)

    @admin.display(description="Preview")
    def large_preview(self, obj: Video):
        if obj.pk is None or obj.youtube_id.startswith(DEMO_VIDEO_PREFIX):
            return "Sample video (no YouTube thumbnail)"
        return thumb(obj.display_thumbnail, 320)

    @admin.display(description="YouTube")
    def watch_link(self, obj: Video):
        if obj.youtube_id.startswith(DEMO_VIDEO_PREFIX):
            return "sample"
        return format_html('<a href="{}" target="_blank" rel="noopener">Watch ↗</a>', obj.youtube_url)


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ("title", "local_time", "duration_minutes", "platform", "status", "is_members_only", "is_published")
    list_editable = ("status", "is_published")
    list_filter = ("status", "platform", "is_members_only", "is_published")
    search_fields = ("title", "description")
    date_hierarchy = "scheduled_at"
    actions = [make_published, make_unpublished, "mark_ended", "mark_cancelled"]
    fieldsets = (
        (None, {"fields": ("title", "description")}),
        ("When & where", {"fields": ("scheduled_at", "duration_minutes", "platform", "stream_url")}),
        ("Visibility", {"fields": ("status", "is_members_only", "is_published")}),
    )

    @admin.display(description="Starts (Bangkok time)", ordering="scheduled_at")
    def local_time(self, obj: LiveStream) -> str:
        return timezone.localtime(obj.scheduled_at).strftime("%a %d %b %Y, %H:%M")

    @admin.action(description="Mark selected as ended")
    def mark_ended(self, request, queryset):
        updated = queryset.update(status=LiveStream.Status.ENDED)
        self.message_user(request, f"Marked {updated} stream(s) as ended.", messages.SUCCESS)

    @admin.action(description="Mark selected as cancelled")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=LiveStream.Status.CANCELLED)
        self.message_user(request, f"Cancelled {updated} stream(s).", messages.SUCCESS)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("cover", "title", "author", "published_at", "is_members_only", "is_published")
    list_display_links = ("cover", "title")
    list_editable = ("is_published",)
    list_filter = ("is_published", "is_members_only", "author")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    readonly_fields = ("created_at", "updated_at")
    actions = [make_published, make_unpublished]
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "body", "cover_image")}),
        ("Publishing", {"fields": ("author", "published_at", "is_members_only", "is_published")}),
        ("History", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="")
    def cover(self, obj: Article):
        return thumb(obj.cover_image.url if obj.cover_image else "", 72)

    def save_model(self, request, obj, form, change):
        if obj.author_id is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)
