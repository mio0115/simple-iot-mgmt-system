"""
DeviceGroup models.
"""

from django.db import models

from account.models import User
from device.models import Device


# Create your models here.
class DeviceGroup(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Description of the device group',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='device_groups'
    )
    devices = models.ManyToManyField(Device, related_name='device_groups')

    def __str__(self):
        return self.name
