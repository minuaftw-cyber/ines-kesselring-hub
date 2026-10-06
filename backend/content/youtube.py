"""
Sync series (playlists) and videos from a YouTube channel.

Uses the YouTube Data API v3 with an API key:
  - playlists.list      -> Series
  - playlistItems.list  -> Video

Rules:
  - New items are created as published.
  - Existing items get fresh titles/thumbnails, but a staff member's
    publish/unpublish choice and manual edits to the slug are kept.
  - Private or deleted videos are skipped.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import Series, Video

logger = logging.getLogger(__name__)

API_BASE = "https://www.googleapis.com/youtube/v3"
RSS_URL = "https://www.youtube.com/feeds/videos.xml"
RSS_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}
SKIPPED_TITLES = {"Private video", "Deleted video"}


class YouTubeSyncError(Exception):
    pass


@dataclass
class SyncResult:
    series_created: int = 0
    series_updated: int = 0
    videos_created: int = 0
    videos_updated: int = 0
    videos_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Series: {self.series_created} new, {self.series_updated} updated. "
            f"Videos: {self.videos_created} new, {self.videos_updated} updated, "
            f"{self.videos_skipped} skipped."
        )


def best_thumbnail(snippet: dict) -> str:
    thumbs = snippet.get("thumbnails") or {}
    for size in ("maxres", "standard", "high", "medium", "default"):
        if thumbs.get(size, {}).get("url"):
            return thumbs[size]["url"]
    return ""


class YouTubeClient:
    def __init__(self, api_key: str, session: requests.Session | None = None, timeout: int = 15):
        if not api_key:
            raise YouTubeSyncError("YOUTUBE_API_KEY is not set.")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get_all(self, endpoint: str, params: dict) -> list[dict]:
        items: list[dict] = []
        page_token = None
        while True:
            query = {**params, "key": self.api_key, "maxResults": 50}
            if page_token:
                query["pageToken"] = page_token
            response = self.session.get(f"{API_BASE}/{endpoint}", params=query, timeout=self.timeout)
            if response.status_code != 200:
                try:
                    message = response.json()["error"]["message"]
                except (ValueError, KeyError, TypeError):
                    message = response.text[:200]
                raise YouTubeSyncError(f"YouTube API {endpoint} failed ({response.status_code}): {message}")
            data = response.json()
            items.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                return items

    def playlists(self, channel_id: str) -> list[dict]:
        return self._get_all("playlists", {"part": "snippet,contentDetails", "channelId": channel_id})

    def playlist_items(self, playlist_id: str) -> list[dict]:
        return self._get_all("playlistItems", {"part": "snippet,contentDetails", "playlistId": playlist_id})


@transaction.atomic
def sync_playlist(client: YouTubeClient, series: Series, result: SyncResult) -> None:
    for position, item in enumerate(client.playlist_items(series.youtube_playlist_id)):
        snippet = item.get("snippet", {})
        details = item.get("contentDetails", {})
        video_id = details.get("videoId")
        published_raw = details.get("videoPublishedAt")
        if not video_id or not published_raw or snippet.get("title") in SKIPPED_TITLES:
            result.videos_skipped += 1
            continue

        values = {
            "title": snippet.get("title", "")[:200],
            "description": snippet.get("description", ""),
            "thumbnail_url": best_thumbnail(snippet),
            "published_at": parse_datetime(published_raw),
            "series": series,
            "position": position,
        }
        _, created = Video.objects.update_or_create(youtube_id=video_id, defaults=values)
        if created:
            result.videos_created += 1
        else:
            result.videos_updated += 1


def sync_channel(
    channel_id: str | None = None,
    api_key: str | None = None,
    playlist_ids: list[str] | None = None,
    client: YouTubeClient | None = None,
) -> SyncResult:
    """Sync every playlist of the channel (or only `playlist_ids`)."""
    channel_id = channel_id or settings.YOUTUBE_CHANNEL_ID
    client = client or YouTubeClient(api_key or settings.YOUTUBE_API_KEY)
    result = SyncResult()

    if playlist_ids is None:
        if not channel_id:
            raise YouTubeSyncError("YOUTUBE_CHANNEL_ID is not set.")
        playlists = client.playlists(channel_id)
    else:
        playlists = [{"id": pid, "snippet": {}} for pid in playlist_ids]

    for playlist in playlists:
        snippet = playlist.get("snippet", {})
        series = Series.objects.filter(youtube_playlist_id=playlist["id"]).first()
        if series is None:
            series = Series(youtube_playlist_id=playlist["id"], title=snippet.get("title") or playlist["id"])
            result.series_created += 1
        else:
            result.series_updated += 1
        if snippet:
            series.title = snippet.get("title", series.title)[:200]
            series.description = snippet.get("description", series.description)
            series.thumbnail_url = best_thumbnail(snippet) or series.thumbnail_url
        series.save()

        try:
            sync_playlist(client, series, result)
        except YouTubeSyncError as exc:
            logger.error("Playlist %s failed: %s", playlist["id"], exc)
            result.errors.append(str(exc))

    logger.info("YouTube sync finished. %s", result.summary())
    return result


def parse_rss(xml_text: str) -> list[dict]:
    """Parse a channel's public RSS feed (latest ~15 uploads, no API key needed)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise YouTubeSyncError(f"Could not read the RSS feed: {exc}") from exc

    entries = []
    for entry in root.findall("atom:entry", RSS_NS):
        video_id = entry.findtext("yt:videoId", default="", namespaces=RSS_NS)
        published = entry.findtext("atom:published", default="", namespaces=RSS_NS)
        group = entry.find("media:group", RSS_NS)
        description, thumbnail = "", ""
        if group is not None:
            description = group.findtext("media:description", default="", namespaces=RSS_NS)
            thumb = group.find("media:thumbnail", RSS_NS)
            thumbnail = thumb.get("url", "") if thumb is not None else ""
        if video_id and published:
            entries.append(
                {
                    "youtube_id": video_id,
                    "title": entry.findtext("atom:title", default="", namespaces=RSS_NS)[:200],
                    "description": description,
                    "thumbnail_url": thumbnail,
                    "published_at": parse_datetime(published),
                }
            )
    return entries


@transaction.atomic
def sync_rss(
    channel_id: str | None = None,
    session: requests.Session | None = None,
    timeout: int = 15,
) -> SyncResult:
    """Add/refresh the latest uploads from the channel RSS feed. Series links are left untouched."""
    channel_id = channel_id or settings.YOUTUBE_CHANNEL_ID
    if not channel_id:
        raise YouTubeSyncError("YOUTUBE_CHANNEL_ID is not set.")
    session = session or requests.Session()
    response = session.get(RSS_URL, params={"channel_id": channel_id}, timeout=timeout)
    if response.status_code != 200:
        raise YouTubeSyncError(f"RSS feed request failed ({response.status_code}).")

    result = SyncResult()
    for item in parse_rss(response.text):
        youtube_id = item.pop("youtube_id")
        _, created = Video.objects.update_or_create(youtube_id=youtube_id, defaults=item)
        if created:
            result.videos_created += 1
        else:
            result.videos_updated += 1
    logger.info("YouTube RSS sync finished. %s", result.summary())
    return result
