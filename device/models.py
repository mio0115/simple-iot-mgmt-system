from django.db import models

from account.models import User


# Create your models here.
class Device(models.Model):
    class DeviceType(models.TextChoices):
        SENSOR = 'sensor', 'Sensor'
        ACTUATOR = 'actuator', 'Actuator'

    class DeviceStatus(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'
        ERROR = 'error', 'Error'

    name = models.CharField(max_length=50)
    device_type = models.CharField(
        choices=DeviceType,
        db_column='type',
        db_comment=(
            'Device role: "Sensor" for data emitters, ',
            '"Actuator" for command receivers.',
        ),
    )
    status = models.CharField(
        choices=DeviceStatus,
        default=DeviceStatus.ONLINE,
        db_comment=(
            'Enumerated device status: "online" when active; ',
            '"offline" when no heartbeat is received whithin the expected interval; ',
            '"error" when the device reports an internal fault.',
        ),
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        db_comment='Timestamp of the last received heartbeat or data message from the device',
    )
    serial_number = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')

    def __str__(self):
        return f'{self.name} ({self.serial_number})'


class DeviceLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='log')
    message = models.CharField(max_length=255, blank=False)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        preview = self.message[:25] + ('...' if len(self.message) > 25 else '')
        return f'{self.device.name}: {preview}'


class DeviceData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='data')
    data = models.CharField(max_length=255, blank=False)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        timestamp = self.created_at.strftime('%Y-%m-%d %H:%M')
        return f'{self.device.name} @ {timestamp}'
