from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Users sign in with their email address instead of a username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    One account type for everyone, with three roles:

    - member: a fan who registered on the website
    - staff:  can sign in to the backoffice and manage content
    - admin:  full access, including user management
    """

    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        STAFF = "staff", "Staff"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField("email address", unique=True)
    display_name = models.CharField(max_length=60, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def role(self) -> str:
        if self.is_superuser:
            return self.Role.ADMIN
        if self.is_staff:
            return self.Role.STAFF
        return self.Role.MEMBER

    @property
    def can_access_backoffice(self) -> bool:
        return self.is_active and self.is_staff
