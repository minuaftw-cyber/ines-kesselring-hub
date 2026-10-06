from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from content.roles import CONTENT_STAFF_GROUP

from .models import User

PASSWORD = "Str0ng-test-pass!"


class AuthApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_register_creates_member_and_returns_token(self):
        response = self.client.post(
            reverse("auth-register"),
            {"email": "Fan@Example.com", "password": PASSWORD, "display_name": "Fan"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["email"], "fan@example.com")
        self.assertEqual(response.data["user"]["role"], "member")
        self.assertFalse(response.data["user"]["can_access_backoffice"])
        self.assertTrue(Token.objects.filter(key=response.data["token"]).exists())

    def test_register_cannot_create_staff(self):
        self.client.post(
            reverse("auth-register"),
            {"email": "sneaky@example.com", "password": PASSWORD, "is_staff": True, "is_superuser": True},
            format="json",
        )
        user = User.objects.get(email="sneaky@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_rejects_duplicate_email_and_weak_password(self):
        User.objects.create_user("taken@example.com", PASSWORD)
        dup = self.client.post(reverse("auth-register"), {"email": "TAKEN@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(dup.status_code, 400)
        weak = self.client.post(reverse("auth-register"), {"email": "new@example.com", "password": "123"}, format="json")
        self.assertEqual(weak.status_code, 400)
        self.assertIn("password", weak.data)

    def test_login_logout_and_me(self):
        User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        bad = self.client.post(reverse("auth-login"), {"email": "staff@example.com", "password": "wrong"}, format="json")
        self.assertEqual(bad.status_code, 400)

        good = self.client.post(reverse("auth-login"), {"email": "STAFF@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(good.status_code, 200)
        self.assertEqual(good.data["user"]["role"], "staff")
        self.assertTrue(good.data["user"]["can_access_backoffice"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {good.data['token']}")
        self.assertEqual(self.client.get(reverse("auth-me")).data["email"], "staff@example.com")

        self.assertEqual(self.client.post(reverse("auth-logout")).status_code, 204)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 401)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 401)

    def test_inactive_user_cannot_log_in(self):
        User.objects.create_user("gone@example.com", PASSWORD, is_active=False)
        response = self.client.post(reverse("auth-login"), {"email": "gone@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_login_is_rate_limited(self):
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "3/min"}):
            codes = [
                self.client.post(
                    reverse("auth-login"), {"email": "x@example.com", "password": "nope"}, format="json"
                ).status_code
                for _ in range(4)
            ]
        self.assertEqual(codes, [400, 400, 400, 429])


class RoleTests(TestCase):
    def test_roles(self):
        self.assertEqual(User.objects.create_user("m@example.com", PASSWORD).role, "member")
        self.assertEqual(User.objects.create_user("s@example.com", PASSWORD, is_staff=True).role, "staff")
        self.assertEqual(User.objects.create_superuser("a@example.com", PASSWORD).role, "admin")

    def test_content_staff_group_exists_with_content_permissions_only(self):
        group = Group.objects.get(name=CONTENT_STAFF_GROUP)
        codenames = set(group.permissions.values_list("codename", flat=True))
        self.assertIn("change_video", codenames)
        self.assertIn("add_article", codenames)
        self.assertNotIn("change_user", codenames)


class BackofficeAccessTests(TestCase):
    """Only staff/admin can open the Django admin; staff cannot manage users."""

    def setUp(self):
        self.member = User.objects.create_user("member@example.com", PASSWORD)
        self.staff = User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.staff.groups.add(Group.objects.get(name=CONTENT_STAFF_GROUP))
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)

    def test_member_is_sent_to_admin_login(self):
        self.client.force_login(self.member)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_staff_can_manage_content_but_not_users(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/admin/content/video/").status_code, 200)
        self.assertEqual(self.client.get("/admin/content/livestream/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 403)

    def test_admin_can_manage_users(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 200)

    def test_admin_login_with_email(self):
        response = self.client.post(
            "/admin/login/?next=/admin/",
            {"username": "staff@example.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
