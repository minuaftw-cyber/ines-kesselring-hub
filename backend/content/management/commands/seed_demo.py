"""
Fill an empty database with sample content so the site can be explored
before YouTube sync is set up. Sample videos use IDs starting with "demo-";
`seed_demo --clear` removes all sample content again.
"""

import os
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from content.models import DEMO_VIDEO_PREFIX, Article, LiveStream, Series, Video
from content.roles import CONTENT_STAFF_GROUP

DEMO_PREFIX = DEMO_VIDEO_PREFIX

SERIES = [
    {
        "title": "Just Chatting",
        "description": "คุยเล่น ตอบคอมเมนต์ และอัปเดตเรื่องราวของช่อง",
        "videos": ["คุยเล่นวันศุกร์ #12", "ตอบคำถามจากคอมเมนต์", "อัปเดตช่องประจำเดือน"],
    },
    {
        "title": "Game Stream",
        "description": "ไลฟ์เกมแบบสบาย ๆ เล่นไปคุยไปกับทุกคน",
        "videos": ["เล่นเกมสยองขวัญครั้งแรก", "ท้าทายด่านยาก", "เกมใหม่ประจำสัปดาห์"],
    },
    {
        "title": "Cover Songs",
        "description": "เพลง cover ทั้งไทยและญี่ปุ่น",
        "videos": ["Cover เพลงญี่ปุ่น", "Acoustic session"],
    },
    {
        "title": "Project EK Dev Log",
        "description": "เบื้องหลังการสร้าง AI VTuber ที่พูดภาษาไทยได้ ตั้งแต่ระบบเสียงจนถึงความจำ",
        "videos": ["Dev Log #1: สถาปัตยกรรมระบบ", "Dev Log #2: ระบบเสียงภาษาไทย", "Dev Log #3: ความจำระยะยาว"],
    },
]

ARTICLES = [
    {
        "title": "Welcome to the new Ines Kesselring hub",
        "excerpt": "เว็บไซต์ใหม่ของช่อง รวมวิดีโอ ตารางไลฟ์ และข่าวสารไว้ในที่เดียว",
        "body": (
            "ยินดีต้อนรับสู่เว็บไซต์ใหม่ของช่อง Ines Kesselring!\n\n"
            "ที่นี่จะรวมวิดีโอทุกซีรีส์ ตารางไลฟ์ล่วงหน้า และข่าวสารล่าสุดไว้ในที่เดียว\n\n"
            "สมัครสมาชิกฟรีเพื่ออ่านบทความเฉพาะสมาชิก และรับข่าวก่อนใคร"
        ),
        "members_only": False,
    },
    {
        "title": "Behind the scenes: how Project EK speaks Thai",
        "excerpt": "เบื้องหลังระบบเสียงภาษาไทยของ Project EK",
        "body": (
            "Project EK ใช้ local LLM ร่วมกับระบบ TTS และ RVC เพื่อให้ตัวละครพูดภาษาไทยได้เป็นธรรมชาติ\n\n"
            "บทความนี้เล่าว่าเสียงเดินทางจากข้อความไปเป็นเสียงพูดได้อย่างไร และปัญหาที่เจอระหว่างทาง\n\n"
            "ส่วนถัดไปจะเจาะลึกเรื่องการลด latency ให้ตอบได้ทันในระหว่างไลฟ์"
        ),
        "members_only": True,
    },
    {
        "title": "Stream schedule update",
        "excerpt": "ตารางไลฟ์เดือนนี้ และเวลาใหม่ของไลฟ์วันเสาร์",
        "body": (
            "เดือนนี้ไลฟ์วันเสาร์จะเลื่อนเป็นสองทุ่มครึ่ง\n\n"
            "ดูตารางทั้งหมดได้ที่หน้า Schedule และกดแจ้งเตือนไว้ใน YouTube ได้เลย"
        ),
        "members_only": False,
    },
]

LIVES = [
    ("Chill chat stream", 2, 20, 120, False),
    ("Game night", 4, 20, 180, False),
    ("Members karaoke", 6, 21, 90, True),
    ("Project EK live test", 9, 19, 120, False),
]


class Command(BaseCommand):
    help = "Create sample content (and optional demo accounts) for local development."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Remove sample content instead.")
        parser.add_argument(
            "--with-users", action="store_true",
            help="Also create demo staff/member accounts using DEMO_PASSWORD from the environment.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.clear()
            return

        if Video.objects.exclude(youtube_id__startswith=DEMO_PREFIX).exists():
            raise CommandError("Real videos already exist — refusing to add sample content.")

        now = timezone.now()
        video_count = 0
        for s_index, data in enumerate(SERIES):
            series, _ = Series.objects.get_or_create(
                title=data["title"],
                defaults={"description": data["description"], "sort_order": s_index},
            )
            for v_index, title in enumerate(data["videos"]):
                Video.objects.get_or_create(
                    youtube_id=f"{DEMO_PREFIX}{s_index}{v_index}",
                    defaults={
                        "title": title,
                        "series": series,
                        "position": v_index,
                        "description": f"{title} — ตัวอย่างวิดีโอในซีรีส์ {series.title}",
                        "published_at": now - timedelta(days=3 * video_count + 1),
                    },
                )
                video_count += 1

        for index, data in enumerate(ARTICLES):
            Article.objects.get_or_create(
                title=data["title"],
                defaults={
                    "excerpt": data["excerpt"],
                    "body": data["body"],
                    "is_members_only": data["members_only"],
                    "is_published": True,
                    "published_at": now - timedelta(days=index * 5),
                },
            )

        today = timezone.localtime(now).replace(minute=0, second=0, microsecond=0)
        for title, days, hour, minutes, members_only in LIVES:
            LiveStream.objects.get_or_create(
                title=title,
                defaults={
                    "scheduled_at": (today + timedelta(days=days)).replace(hour=hour),
                    "duration_minutes": minutes,
                    "is_members_only": members_only,
                    "stream_url": "https://www.youtube.com/@InesKesselring/streams",
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Sample content ready: {Series.objects.count()} series, {video_count} videos, "
            f"{len(ARTICLES)} articles, {len(LIVES)} live streams."
        ))

        if options["with_users"]:
            self.create_users()

    def create_users(self):
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            raise CommandError("Set DEMO_PASSWORD in backend/.env to create demo accounts.")
        staff_group = Group.objects.get(name=CONTENT_STAFF_GROUP)
        accounts = [
            ("staff@example.com", "Demo Staff", True),
            ("member@example.com", "Demo Member", False),
        ]
        for email, name, is_staff in accounts:
            user, created = User.objects.get_or_create(
                email=email, defaults={"display_name": name, "is_staff": is_staff}
            )
            if created:
                user.set_password(password)
                user.save()
            if is_staff:
                user.groups.add(staff_group)
            self.stdout.write(f"{'Created' if created else 'Kept'} {email}")

    def clear(self):
        videos, _ = Video.objects.filter(youtube_id__startswith=DEMO_PREFIX).delete()
        empty_series = Series.objects.filter(youtube_playlist_id__isnull=True, videos__isnull=True)
        series, _ = empty_series.delete()
        articles, _ = Article.objects.filter(title__in=[a["title"] for a in ARTICLES]).delete()
        lives, _ = LiveStream.objects.filter(title__in=[l[0] for l in LIVES]).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Removed sample content ({videos} videos, {series} series, {articles} articles, {lives} lives)."
        ))
