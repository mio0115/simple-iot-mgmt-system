"""
Account models.
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


# Create your models here.
class UserManager(BaseUserManager):
    """Manager for users."""

    def _create_user(self, email, password, **extra_field):
        """Create, save, and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_field)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_field):
        """Set default of extra_field and pass it to _create_user."""
        extra_field.setdefault('is_staff', False)
        extra_field.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_field)

    def create_superuser(self, email, password, **extra_field):
        """Set and check the authentication and pass it to _create_user"""
        extra_field.setdefault('is_staff', True)
        extra_field.setdefault('is_superuser', True)

        if not extra_field['is_staff']:
            raise ValueError('Superuser must have is_staff as True')
        if not extra_field['is_superuser']:
            raise ValueError('Superuser must have is_superuser as True')
        return self._create_user(email, password, **extra_field)


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name
