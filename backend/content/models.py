from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def unique_slug(instance, value: str, field: str = "slug", max_length: int = 80) -> str:
    """Build a URL-safe slug that is unique for the model (Thai titles fall back to an id)."""
    base = slugify(value, allow_unicode=False)[:max_length].strip("-") or instance.__class__.__name__.lower()
    model = instance.__class__
    slug, n = base, 2
    while model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        suffix = f"-{n}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
        n += 1
    return slug


# Sample videos created by `seed_demo` use this prefix instead of a real YouTube ID.
DEMO_VIDEO_PREFIX = "demo-"


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Series(TimeStamped):
    """A group of videos — usually mirrors a YouTube playlist."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.TextField(blank=True)
    youtube_playlist_id = models.CharField(
        max_length=64, unique=True, null=True, blank=True,
        help_text="Filled automatically by YouTube sync. Leave empty for a manual series.",
    )
    thumbnail_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "-created_at"]
        verbose_name_plural = "series"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)


class Video(TimeStamped):
    series = models.ForeignKey(
        Series, related_name="videos", on_delete=models.SET_NULL, null=True, blank=True
    )
    youtube_id = models.CharField("YouTube video ID", max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    position = models.PositiveIntegerField(default=0, help_text="Order inside the series.")
    is_published = models.BooleanField(default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def display_thumbnail(self) -> str:
        return self.thumbnail_url or f"https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg"


class LiveStream(TimeStamped):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live now"
        ENDED = "ended", "Ended"
        CANCELLED = "cancelled", "Cancelled"

    class Platform(models.TextChoices):
        YOUTUBE = "youtube", "YouTube"
        TIKTOK = "tiktok", "TikTok"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=120)
    platform = models.CharField(max_length=20, choices=Platform.choices, default=Platform.YOUTUBE)
    stream_url = models.URLField(blank=True, help_text="Link to the stream or waiting room.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    is_members_only = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self) -> str:
        return f"{self.title} ({timezone.localtime(self.scheduled_at):%Y-%m-%d %H:%M})"

    @property
    def ends_at(self):
        return self.scheduled_at + timedelta(minutes=self.duration_minutes)


def article_cover_path(instance, filename: str) -> str:
    return f"articles/{timezone.now():%Y/%m}/{filename}"


class Article(TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    excerpt = models.CharField(max_length=300, blank=True, help_text="Short summary shown in lists.")
    body = models.TextField(help_text="Separate paragraphs with an empty line.")
    cover_image = models.ImageField(upload_to=article_cover_path, blank=True)
    author = models.ForeignKey(
        "accounts.User", related_name="articles", on_delete=models.SET_NULL, null=True, blank=True
    )
    is_members_only = models.BooleanField(
        default=False, help_text="Only signed-in members can read the full article."
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)
