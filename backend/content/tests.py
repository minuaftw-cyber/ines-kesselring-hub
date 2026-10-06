from datetime import timedelta
from unittest.mock import MagicMock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User

from .models import Article, LiveStream, Series, Video
from .youtube import YouTubeClient, YouTubeSyncError, parse_rss, sync_channel, sync_rss


def fake_response(status=200, json_data=None, text=""):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = json_data or {}
    response.text = text
    return response


class PublicApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.series = Series.objects.create(title="Game Stream")
        Series.objects.create(title="Hidden", is_published=False)
        Video.objects.create(youtube_id="abc123", title="Visible", series=self.series)
        Video.objects.create(youtube_id="def456", title="Draft", series=self.series, is_published=False)

    def test_series_list_only_published_with_counts(self):
        data = self.client.get("/api/series/").json()
        self.assertEqual([s["title"] for s in data], ["Game Stream"])
        self.assertEqual(data[0]["video_count"], 1)
        self.assertEqual(data[0]["thumbnail"], "https://i.ytimg.com/vi/abc123/hqdefault.jpg")

    def test_series_follow_sort_order(self):
        Series.objects.create(title="First", sort_order=0)
        Series.objects.filter(pk=self.series.pk).update(sort_order=5)
        Series.objects.create(title="Middle", sort_order=2)
        titles = [s["title"] for s in self.client.get("/api/series/").json()]
        self.assertEqual(titles, ["First", "Middle", "Game Stream"])

    def test_series_detail_hides_unpublished_videos(self):
        data = self.client.get(f"/api/series/{self.series.slug}/").json()
        self.assertEqual([v["youtube_id"] for v in data["videos"]], ["abc123"])
        self.assertEqual(self.client.get("/api/series/hidden/").status_code, 404)

    def test_video_list_paginated_and_filterable(self):
        data = self.client.get("/api/videos/").json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["series"], {"slug": "game-stream", "title": "Game Stream"})
        self.assertEqual(self.client.get("/api/videos/?series=nope").json()["count"], 0)

    def test_health(self):
        data = self.client.get("/api/health/").json()
        self.assertEqual(data["status"], "ok")


class ScheduleTests(TestCase):
    def test_upcoming_only_and_members_link_hidden(self):
        now = timezone.now()
        LiveStream.objects.create(title="Past", scheduled_at=now - timedelta(days=2))
        LiveStream.objects.create(title="Soon", scheduled_at=now + timedelta(days=1), stream_url="https://y.t/soon")
        LiveStream.objects.create(
            title="Members", scheduled_at=now + timedelta(days=2),
            is_members_only=True, stream_url="https://y.t/secret",
        )
        LiveStream.objects.create(title="Hidden", scheduled_at=now + timedelta(days=3), is_published=False)

        client = APIClient()
        data = client.get("/api/schedule/").json()
        self.assertEqual([s["title"] for s in data], ["Soon", "Members"])
        self.assertEqual(data[1]["stream_url"], "")

        member = User.objects.create_user("m@example.com", "Str0ng-test-pass!")
        client.force_authenticate(member)
        self.assertEqual(client.get("/api/schedule/").json()[1]["stream_url"], "https://y.t/secret")

        past = client.get("/api/schedule/?past=1").json()
        self.assertEqual([s["title"] for s in past], ["Past"])


class ArticleTests(TestCase):
    def setUp(self):
        self.public = Article.objects.create(title="Hello", body="One\n\nTwo", is_published=True)
        self.members = Article.objects.create(
            title="Secret", body="Teaser paragraph\n\nHidden paragraph", is_published=True, is_members_only=True
        )
        Article.objects.create(title="Draft", body="x", is_published=False)
        Article.objects.create(
            title="Scheduled", body="x", is_published=True, published_at=timezone.now() + timedelta(days=1)
        )

    def test_list_hides_drafts_and_future_posts(self):
        titles = [a["title"] for a in APIClient().get("/api/articles/").json()["results"]]
        self.assertEqual(sorted(titles), ["Hello", "Secret"])

    def test_members_only_article_is_locked_for_guests(self):
        data = APIClient().get(f"/api/articles/{self.members.slug}/").json()
        self.assertTrue(data["locked"])
        self.assertEqual(data["body"], "Teaser paragraph")

    def test_members_only_article_unlocked_for_members(self):
        client = APIClient()
        client.force_authenticate(User.objects.create_user("m@example.com", "Str0ng-test-pass!"))
        data = client.get(f"/api/articles/{self.members.slug}/").json()
        self.assertFalse(data["locked"])
        self.assertIn("Hidden paragraph", data["body"])

    def test_slug_generated_and_unique(self):
        a = Article.objects.create(title="Same title", body="x")
        b = Article.objects.create(title="Same title", body="x")
        thai = Article.objects.create(title="ข่าวภาษาไทย", body="x")
        self.assertEqual(a.slug, "same-title")
        self.assertEqual(b.slug, "same-title-2")
        self.assertTrue(thai.slug)


PLAYLISTS = {
    "items": [
        {"id": "PL1", "snippet": {"title": "Game Stream", "description": "Games",
                                  "thumbnails": {"high": {"url": "https://img/pl1.jpg"}}}},
    ]
}
PLAYLIST_ITEMS_PAGE_1 = {
    "nextPageToken": "next",
    "items": [
        {"snippet": {"title": "Episode 1", "description": "d1", "thumbnails": {"medium": {"url": "https://img/v1.jpg"}}},
         "contentDetails": {"videoId": "vid1", "videoPublishedAt": "2026-01-01T10:00:00Z"}},
        {"snippet": {"title": "Private video"}, "contentDetails": {"videoId": "vidX"}},
    ],
}
PLAYLIST_ITEMS_PAGE_2 = {
    "items": [
        {"snippet": {"title": "Episode 2", "thumbnails": {}},
         "contentDetails": {"videoId": "vid2", "videoPublishedAt": "2026-01-08T10:00:00Z"}},
    ],
}


class YouTubeSyncTests(TestCase):
    def make_client(self):
        session = MagicMock()

        def get(url, params, timeout):
            if url.endswith("/playlists"):
                return fake_response(json_data=PLAYLISTS)
            if params.get("pageToken") == "next":
                return fake_response(json_data=PLAYLIST_ITEMS_PAGE_2)
            return fake_response(json_data=PLAYLIST_ITEMS_PAGE_1)

        session.get.side_effect = get
        return YouTubeClient("test-key", session=session)

    def test_sync_creates_series_and_videos_across_pages(self):
        result = sync_channel(channel_id="UC123", client=self.make_client())
        self.assertEqual((result.series_created, result.videos_created, result.videos_skipped), (1, 2, 1))
        series = Series.objects.get(youtube_playlist_id="PL1")
        self.assertEqual(series.thumbnail_url, "https://img/pl1.jpg")
        self.assertEqual(list(series.videos.order_by("position").values_list("youtube_id", flat=True)), ["vid1", "vid2"])

    def test_resync_keeps_staff_publish_choice(self):
        sync_channel(channel_id="UC123", client=self.make_client())
        Video.objects.filter(youtube_id="vid1").update(is_published=False, title="old")
        result = sync_channel(channel_id="UC123", client=self.make_client())
        video = Video.objects.get(youtube_id="vid1")
        self.assertEqual(result.videos_updated, 2)
        self.assertFalse(video.is_published)
        self.assertEqual(video.title, "Episode 1")

    def test_api_error_is_reported(self):
        session = MagicMock()
        session.get.return_value = fake_response(403, {"error": {"message": "quota exceeded"}})
        with self.assertRaisesMessage(YouTubeSyncError, "quota exceeded"):
            sync_channel(channel_id="UC123", client=YouTubeClient("k", session=session))

    def test_missing_key(self):
        with self.assertRaises(YouTubeSyncError):
            YouTubeClient("")


RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <title>Ines Kesselring</title>
  <entry>
    <yt:videoId>rss1</yt:videoId>
    <title>Latest upload</title>
    <published>2026-09-30T12:00:00+00:00</published>
    <media:group>
      <media:thumbnail url="https://i4.ytimg.com/vi/rss1/hqdefault.jpg" width="480" height="360"/>
      <media:description>Hello everyone</media:description>
    </media:group>
  </entry>
</feed>"""


class RssSyncTests(TestCase):
    def test_parse_rss(self):
        entries = parse_rss(RSS)
        self.assertEqual(entries[0]["youtube_id"], "rss1")
        self.assertEqual(entries[0]["description"], "Hello everyone")

    def test_sync_rss_creates_then_updates(self):
        session = MagicMock()
        session.get.return_value = fake_response(text=RSS)
        self.assertEqual(sync_rss("UC123", session=session).videos_created, 1)
        self.assertEqual(sync_rss("UC123", session=session).videos_updated, 1)
        self.assertEqual(Video.objects.get(youtube_id="rss1").title, "Latest upload")

    def test_bad_feed(self):
        with self.assertRaises(YouTubeSyncError):
            parse_rss("not xml")


@override_settings(YOUTUBE_CHANNEL_ID="")
class SeedTests(TestCase):
    def test_seed_and_clear(self):
        call_command("seed_demo", stdout=MagicMock())
        self.assertGreater(Video.objects.count(), 5)
        self.assertEqual(APIClient().get("/api/videos/").json()["results"][0]["thumbnail"], "")
        call_command("seed_demo", "--clear", stdout=MagicMock())
        self.assertEqual(Video.objects.count(), 0)
        self.assertEqual(Series.objects.count(), 0)
