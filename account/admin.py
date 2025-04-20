"""
Django admin customization.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Custom UserCreationForm due to customized User model."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ('email', 'name')


class UserChangeForm(BaseUserChangeForm):
    """Custom UserChangeForm due to customized User model"""

    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = ('email', 'name', 'is_active', 'is_staff')


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""

    form = UserChangeForm
    add_form = UserCreationForm

    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'name', 'password1', 'password2'),
            },
        ),
    )
    readonly_fields = ['last_login']


admin.site.register(User, UserAdmin)
