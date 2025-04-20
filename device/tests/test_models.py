"""
Test for models in device.
"""

from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from account.tests.factories import UserFactory

from ..models import DeviceData, DeviceLog
from .factories import DeviceDataFactory, DeviceFactory, DeviceLogFactory


class DeviceTests(TestCase):
    """Tests for the Device model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_str_returns_name_and_serial(self):
        """
        Return "<device_name> (<serial_number>)" as the string representation.
        """
        device = DeviceFactory(owner=self.user)
        self.assertEqual(str(device), f'{device.name} ({device.serial_number})')

    def test_owner_fk_links_user_and_reverse(self):
        """
        Ensure owner FK is set correctly and reverse lookup returns this device.
        """
        device = DeviceFactory(owner=self.user)
        # Forward relationship
        self.assertEqual(self.user, device.owner)
        # Reverse relation via related_name 'devices'
        self.assertIn(device, self.user.devices.all())

    def test_cascade_delete_removes_devices(self):
        """
        Deleting a User should cascade and delete its Device entries.
        """
        device = DeviceFactory(owner=self.user)
        self.user.delete()
        self.assertFalse(
            DeviceFactory._meta.model.objects.filter(pk=device.pk).exists()
        )


class DeviceLogTests(TestCase):
    """Tests for DeviceLog model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.device = DeviceFactory(owner=cls.user)

    def test_str_returns_device_name_and_message(self):
        """
        Return "<device_name>: <message or truncated message>" as the string representation.
        """
        # Short message case
        log_short = DeviceLogFactory(device=self.device, message='Short message')
        self.assertEqual(str(log_short), f'{self.device.name}: Short message')

        # Long message case (>25 chars)
        long_msg = 'x' * 30
        log_long = DeviceLogFactory(device=self.device, message=long_msg)
        expected = f'{self.device.name}: {long_msg[:25]}...'
        self.assertEqual(str(log_long), expected)

    def test_device_fk_and_reverse(self):
        """
        Ensure device FK is set correctly and reverse lookup returns this log.
        """
        log = DeviceLogFactory(device=self.device)
        # Forward relation
        self.assertEqual(self.device, log.device)
        # Reverse relation
        self.assertIn(log, self.device.log.all())

    def test_cascade_delete_removes_logs(self):
        """
        Deleting a Device should cascade and delete its DeviceLog entries.
        """
        log = DeviceLogFactory(device=self.device)
        self.device.delete()
        self.assertFalse(DeviceLog.objects.filter(pk=log.pk).exists())


class DeviceDataTests(TestCase):
    """Tests DeviceData model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.device = DeviceFactory(owner=cls.user)

    def test_str_returns_device_name_and_created_at(self):
        """
        Return "<device_name> @ <YYYYMMDD HHMM>" as the string representation.
        """
        fixed_dt = datetime(2025, 4, 19, 00, 30, tzinfo=timezone.get_default_timezone())
        with patch('django.utils.timezone.now', return_value=fixed_dt):
            device_data = DeviceDataFactory(device=self.device)

        expected = f'{device_data.device.name} @ {fixed_dt.strftime("%Y-%m-%d %H:%M")}'
        self.assertEqual(str(device_data), expected)

    def test_device_fk_and_reverse(self):
        """
        Ensure device FK is set correctly and reverse lookup returns data.
        """
        device_data = DeviceDataFactory(device=self.device)
        # Forward relation
        self.assertEqual(self.device, device_data.device)
        # Reverse relation
        self.assertIn(device_data, self.device.data.all())

    def test_cascade_delete_removes_data(self):
        """
        Deleting a Device should cascade and delete its DeviceData entries.
        """
        data = DeviceDataFactory(device=self.device)
        self.device.delete()
        self.assertFalse(DeviceData.objects.filter(pk=data.pk).exists())
