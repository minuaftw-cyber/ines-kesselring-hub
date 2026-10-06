from django.core.management.base import BaseCommand, CommandError

from content.youtube import YouTubeSyncError, sync_channel, sync_rss


class Command(BaseCommand):
    help = (
        "Sync videos from the YouTube channel. "
        "Default uses the YouTube Data API (needs YOUTUBE_API_KEY) and imports playlists as series. "
        "--rss uses the public feed (no key) and imports the latest uploads only."
    )

    def add_arguments(self, parser):
        parser.add_argument("--rss", action="store_true", help="Use the public RSS feed (no API key).")
        parser.add_argument("--channel", help="Channel ID (defaults to YOUTUBE_CHANNEL_ID).")
        parser.add_argument(
            "--playlist", action="append", dest="playlists",
            help="Only sync this playlist ID (repeatable). API mode only.",
        )

    def handle(self, *args, **options):
        try:
            if options["rss"]:
                result = sync_rss(channel_id=options["channel"])
            else:
                result = sync_channel(channel_id=options["channel"], playlist_ids=options["playlists"])
        except YouTubeSyncError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(result.summary()))
        for error in result.errors:
            self.stderr.write(self.style.WARNING(error))
