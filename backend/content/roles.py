"""
The "Content Staff" group: what a staff member may do in the backoffice.

Staff can manage series, videos, the live schedule and news, but cannot
manage user accounts (only admins/superusers can). The group is created or
refreshed automatically after every `migrate`.
"""

from django.apps import apps as global_apps

CONTENT_STAFF_GROUP = "Content Staff"
CONTENT_MODELS = ["series", "video", "livestream", "article"]


def ensure_content_staff_group(sender=None, apps=global_apps, **kwargs):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_types = ContentType.objects.filter(app_label="content", model__in=CONTENT_MODELS)
    permissions = Permission.objects.filter(content_type__in=content_types)
    if not permissions.exists():
        return  # permissions are not created yet (first migrate pass)

    group, _ = Group.objects.get_or_create(name=CONTENT_STAFF_GROUP)
    group.permissions.set(permissions)
