from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class EmailUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "display_name")


class EmailUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = EmailUserChangeForm
    add_form = EmailUserCreationForm

    list_display = ("email", "display_name", "role_badge", "is_active", "date_joined", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "display_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "first_name", "last_name")}),
        (
            "Role & permissions",
            {
                "description": (
                    "Staff can sign in to this backoffice. Add staff to the "
                    "“Content Staff” group so they can manage videos, schedule and news. "
                    "Superusers (admins) have full access."
                ),
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Activity", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "display_name", "password1", "password2", "is_staff", "groups"),
            },
        ),
    )

    @admin.display(description="Role", ordering="is_superuser")
    def role_badge(self, obj: User) -> str:
        return User.Role(obj.role).label
