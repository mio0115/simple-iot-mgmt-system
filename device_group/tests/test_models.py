"""
Tests for models in device_group.
"""

from django.test import TestCase

from account.tests.factories import UserFactory
from device.tests.factories import DeviceFactory

from .factories import DeviceGroupFactory


class DeviceGroupTests(TestCase):
    """Tests for the DeviceGroup model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.device_1 = DeviceFactory(owner=cls.user)
        cls.device_2 = DeviceFactory(owner=cls.user)
        cls.device_3 = DeviceFactory(owner=cls.user)

    def test_str_returns_group_name(self):
        """
        Return "<group name>" as the string representation.
        """
        group = DeviceGroupFactory(
            owner=self.user, devices=[self.device_1, self.device_2]
        )
        self.assertEqual(str(group), group.name)

    def test_owner_fk_and_reverse(self):
        """
        Ensure owner FK is set correctly and reverse lookup returns this group.
        """
        group = DeviceGroupFactory(
            owner=self.user, devices=[self.device_1, self.device_2]
        )
        # Forward relation
        self.assertEqual(self.user, group.owner)
        # Reverse relation
        self.assertIn(group, self.user.device_groups.all())

    def test_devices_m2m_forward_relationship(self):
        """
        Include assigned devices in the group's devices queryset in ID order.
        """
        group = DeviceGroupFactory(
            owner=self.user, devices=[self.device_1, self.device_2]
        )

        expected = {self.device_1, self.device_2}
        self.assertQuerySetEqual(
            group.devices.order_by('id'),
            [d for d in sorted(expected, key=lambda x: x.id)],
            ordered=True,
        )

    def test_devices_m2m_reverse_counts(self):
        """
        Match device_groups count to the number of groups each device belongs to.
        """
        DeviceGroupFactory(owner=self.user, devices=[self.device_1, self.device_2])
        DeviceGroupFactory(owner=self.user, devices=[self.device_2, self.device_3])

        self.assertEqual(self.device_2.device_groups.count(), 2)
        self.assertEqual(self.device_3.device_groups.count(), 1)

    def test_empty_group_has_no_devices(self):
        """
        Create a new group with no devices and verify its devices queryset is empty.
        """
        empty = DeviceGroupFactory(owner=self.user, devices=[])
        self.assertFalse(empty.devices.exists())

    def test_adding_duplicate_device_is_idempotent(self):
        """
        Adding the same device twice should not duplicate it in the devices relation.
        """
        group = DeviceGroupFactory(owner=self.user)
        group.devices.set([self.device_1, self.device_1])
        self.assertEqual(group.devices.count(), 1)
