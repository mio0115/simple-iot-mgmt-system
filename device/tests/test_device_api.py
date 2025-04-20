"""
Tests for api endpoints about Device.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from account.tests.factories import UserFactory

from ..models import Device
from .factories import DeviceFactory


class DeviceAPITests(APITestCase):
    """Tests for the Device API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.devices = DeviceFactory.create_batch(5, owner=cls.user)

    def setUp(self):
        # Use DRF's APIClient and authenticate
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_devices(self):
        """
        GET /api/devices/ returns all devices.
        """
        url = reverse('device:device-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if return exactly 5 items
        self.assertEqual(len(response.data), len(self.devices))

        for dev, payload in zip(self.devices, response.data):
            self.assertEqual(payload['serial_number'], dev.serial_number)

    def test_create_device(self):
        """
        POST /api/devices/ returns all devices.
        """
        url = reverse('device:device-list')
        new_data = {
            'name': 'new sensor',
            'device_type': Device.DeviceType.SENSOR,
            'status': Device.DeviceStatus.ONLINE,
            'serial_number': 'ABC123',
            'owner': self.user.pk,
        }
        response = self.client.post(url, new_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Response payload matches the input
        self.assertEqual(response.data['serial_number'], new_data['serial_number'])
        # Check that if the device really exists in the DB
        self.assertTrue(Device.objects.filter(serial_number='ABC123').exists())

    def test_get_device(self):
        """
        GET /api/devices/{pk}/ returns a single device.
        """
        target = self.devices[0]
        url = reverse('device:device-detail', kwargs={'pk': target.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if device in response match target device
        self.assertEqual(response.data['id'], target.pk)
        self.assertEqual(response.data['serial_number'], target.serial_number)

    def test_update_device(self):
        """
        PUT /api/devices/{pk}/ updates the device.
        """
        target = self.devices[1]
        url = reverse('device:device-detail', kwargs={'pk': target.pk})
        updated_data = {
            'name': target.name,
            'device_type': target.device_type,
            'status': Device.DeviceStatus.OFFLINE,
            'serial_number': target.serial_number,
            'owner': target.owner.pk,
        }
        response = self.client.put(url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the device is updated
        target.refresh_from_db()
        self.assertEqual(target.status, Device.DeviceStatus.OFFLINE)

    def test_delete_device(self):
        """
        DELETE /api/deivces/{pk}/ delete the device.
        """
        target = self.devices[-1]
        url = reverse('device:device-detail', kwargs={'pk': target.pk})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check if the device dropped from the DB
        self.assertFalse(
            Device.objects.filter(serial_number=target.serial_number).exists()
        )


class DeviceAccessControlTests(APITestCase):
    """Ensure device API enforces object-level permissions on every endpoint."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.user_dev = DeviceFactory(owner=cls.user)
        cls.other_dev = DeviceFactory(owner=cls.other_user)

    def setUp(self):
        self.client = APIClient()

    def test_list_devices_requires_authentication(self):
        """
        GET /api/devices/ 200 for auth; 401 for anon.
        """
        url = reverse('device:device-list')

        # Check if we get 401 from anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if we get 200 from authentication
        self.client.force_authenticate(self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_device_requires_authentication(self):
        """
        POST /api/devices/ 201 for auth, 401 for anon.
        """
        url = reverse('device:device-list')
        new_data = {
            'name': 'new sensor',
            'device_type': Device.DeviceType.SENSOR,
            'status': Device.DeviceStatus.ONLINE,
            'serial_number': 'ABC123',
            'owner': self.user.pk,
        }

        response = self.client.post(url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.user)
        response = self.client.post(url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_device_object_level_authentication(self):
        """
        GET /api/devices/{pk}/ 200 for own, 403 for other.
        """
        url_user = reverse('device:device-detail', kwargs={'pk': self.user_dev.pk})
        url_other = reverse('device:device-detail', kwargs={'pk': self.other_dev.pk})

        self.client.force_authenticate(self.user)

        # Check if we get 200 while access own device
        response = self.client.get(url_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if we get 403 while access other's device
        response = self.client.get(url_other, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_device_object_level_authentication(self):
        """
        PUT /api/devices/{pk}/ 200 for own, 403 for other.
        """
        url_user = reverse('device:device-detail', kwargs={'pk': self.user_dev.pk})
        url_other = reverse('device:device-detail', kwargs={'pk': self.other_dev.pk})
        payload_user = {
            'name': self.user_dev.name,
            'device_type': self.user_dev.device_type,
            'status': Device.DeviceStatus.OFFLINE,
            'serial_number': self.user_dev.serial_number,
            'owner': self.user_dev.owner.pk,
        }
        payload_other = {
            'name': self.other_dev.name,
            'device_type': self.other_dev.device_type,
            'status': Device.DeviceStatus.OFFLINE,
            'serial_number': self.other_dev.serial_number,
            'owner': self.other_dev.owner.pk,
        }

        self.client.force_authenticate(self.user)

        # Check if we get 200 while access own device
        response = self.client.put(url_user, payload_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if we get 403 while access other's device
        response = self.client.put(url_other, payload_other, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_device_object_level_authentication(self):
        """
        DELETE /api/devices/{pk}/ 204 for own, 403 for other.
        """
        url_user = reverse('device:device-detail', kwargs={'pk': self.user_dev.pk})
        url_other = reverse('device:device-detail', kwargs={'pk': self.other_dev.pk})

        self.client.force_authenticate(self.user)

        # Check if we get 204 while access own device
        response = self.client.delete(url_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check if we get 403 while access other's device
        response = self.client.delete(url_other, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
