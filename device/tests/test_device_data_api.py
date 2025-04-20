"""
Tests for api endpoints about DeviceData.
"""

from datetime import datetime
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from account.tests.factories import UserFactory

from ..models import Device, DeviceData
from .factories import DeviceDataFactory, DeviceFactory


class DeviceDataAPITests(APITestCase):
    """Tests for the DeviceData API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.device = DeviceFactory(owner=cls.user)

        fixed_dt = datetime(2025, 4, 1, 8, 0, tzinfo=timezone.get_default_timezone())
        with patch('django.utils.timezone.now', return_value=fixed_dt):
            cls.data_1 = DeviceDataFactory(device=cls.device, data='10')

        fixed_dt = datetime(2025, 4, 1, 12, 0, tzinfo=timezone.get_default_timezone())
        with patch('django.utils.timezone.now', return_value=fixed_dt):
            cls.data_2 = DeviceDataFactory(device=cls.device, data='20')

        fixed_dt = datetime(2025, 4, 1, 18, 0, tzinfo=timezone.get_default_timezone())
        with patch('django.utils.timezone.now', return_value=fixed_dt):
            cls.data_3 = DeviceDataFactory(device=cls.device, data='30')

    def setUp(self):
        # Use DRF's APIClient and authenticate
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_all_data(self):
        """
        Authenticated GET without params returns all data for own device.
        """
        url = reverse('device:device-data', kwargs={'pk': self.device.pk})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expect 3 records
        self.assertEqual(len(response.data), 3)
        # Check timestamps sorted
        timestamps = [item['created_at'] for item in response.data]
        self.assertListEqual(timestamps, sorted(timestamps))

    def test_get_data_with_time_interval(self):
        """
        GET with ?start=&end= filters data via __range lookup.
        """
        url = reverse('device:device-data', kwargs={'pk': self.device.pk})
        params = {'start': '2025-04-01T09:00:00Z', 'end': '2025-04-01T17:00:00Z'}
        response = self.client.get(url, params, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only data_2 (12:00) falls between 09:00 and 17:00
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['data'], '20')

    def test_get_data_with_invalid_time_interval(self):
        pass

    def test_add_data_to_online_device(self):
        """
        POST /api/devices/{id}/data/ returns 201 and all data if device is ONLINE.
        """
        url = reverse('device:device-data', kwargs={'pk': self.device.pk})
        new_data = {'device': self.device.pk, 'data': 'ABC123'}
        response = self.client.post(url, new_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check if the data really exists in the DB
        self.assertTrue(
            DeviceData.objects.filter(
                device=self.device.pk, data=new_data['data']
            ).exists()
        )

    def test_add_data_to_offline_or_error_device(self):
        """
        POST /api/devices/{id}/data/ returns 409 if device is either OFFLINE or ERROR.
        """
        # Suppose that device.status is OFFLINE
        offline_dev = DeviceFactory(status=Device.DeviceStatus.OFFLINE, owner=self.user)
        new_data = {'device': offline_dev.pk, 'data': 'ABC123'}
        url = reverse('device:device-data', kwargs={'pk': offline_dev.pk})
        response = self.client.post(url, new_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        # Check if the data exists in the DB
        self.assertFalse(
            DeviceData.objects.filter(device=offline_dev.pk, data=new_data['data'])
        )

        # Suppose that device.status is ERROR
        error_dev = DeviceFactory(status=Device.DeviceStatus.ERROR, owner=self.user)
        new_data['device'] = error_dev.pk
        url = reverse('device:device-data', kwargs={'pk': error_dev.pk})
        response = self.client.post(url, new_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        # Check if the data exists in the DB
        self.assertFalse(
            DeviceData.objects.filter(device=error_dev.pk, data=new_data['data'])
        )


class DeviceDataAccessControlTests(APITestCase):
    """Ensure device-data API enforces object-level permissions on every endpoint."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.user_dev = DeviceFactory(owner=cls.user)
        cls.other_dev = DeviceFactory(owner=cls.other_user)

    def setUp(self):
        self.client = APIClient()

    def test_list_data_requires_authentication(self):
        """
        GET /api/devices/{id}/data/ 200 for auth; 401 for anon.
        """
        url = reverse('device:device-data', kwargs={'pk': self.user_dev.pk})

        # Check if we get 401 from anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if we get 200 from authentication
        self.client.force_authenticate(self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_data_requires_authentication(self):
        """
        POST /api/devices/{id}/data/ 201 for auth, 401 for anon.
        """
        url = reverse('device:device-data', kwargs={'pk': self.user_dev.pk})
        new_data = {'device': self.user_dev.pk, 'data': '10'}

        # Check if we get 401 from anonymous
        response = self.client.post(url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if we get 200 from authentication
        self.client.force_authenticate(self.user)
        response = self.client.get(url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_data_object_level_authentication(self):
        """
        GET /api/devices/{id}/data/ 200 for own; 403 for other.
        """
        own_url = reverse('device:device-data', kwargs={'pk': self.user_dev.pk})
        other_url = reverse('device:device-data', kwargs={'pk': self.other_dev.pk})

        self.client.force_authenticate(self.user)

        # Check if we get 200 while access own device
        response = self.client.get(own_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if we get 403 while access other device
        response = self.client.get(other_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_data_object_level_authentication(self):
        """
        POST /api/devices/{id}/data/ 201 for own; 403 for other.
        """
        own_url = reverse('device:device-data', kwargs={'pk': self.user_dev.pk})
        other_url = reverse('device:device-data', kwargs={'pk': self.other_dev.pk})

        self.client.force_authenticate(self.user)

        new_data = {'device': self.user_dev.pk, 'data': '10'}
        # Check if we get 201 while access own device
        response = self.client.post(own_url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if we get 403 while access other deivce
        new_data['device'] = self.other_dev.pk
        response = self.client.post(other_url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
