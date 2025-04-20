"""
View functions in device.
"""

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from .models import Device, DeviceData
from .permissions import IsDataOwner, IsOwner


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'device_type',
            'status',
            'last_seen',
            'serial_number',
            'owner',
        ]
        read_only_fields = ['id', 'owner']


class DeviceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceData
        fields = ['id', 'device', 'data', 'created_at']
        read_only_fields = ['id', 'device', 'created_at']


class DeviceStatusConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Cannot add data: device is offline or in error state.'
    default_code = 'device_offline_conflict'


class DeviceListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/devices/  return 200 + all-devices owned by user if auth; 401 otherwise.
    POST /api/devices/ return 201 if auth and created; 401 otherwise.
    """

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return devices owned by the authenticated user
        return Device.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Ensure that new devices are created with the current user as owner
        serializer.save(owner=self.request.user)


class DeviceGetUpdateDropAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/devices/{pk}/    return 200 + device if owned by user; 404 if not owned; 401 if anon.
    PUT /api/devices/{pk}/    return 200 if owned and updated; 404 if not owned; 401 if anon.
    DELETE /api/devices/{pk}/ return 204 if owned and deleted; 404 if not owned; 401 if anon.
    """

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)


class DeviceDataListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/devices/{pk}/data/?start=<ISO>&end=<ISO> return 200 + device-data if valid; 404 if not owned; 401 if anon.
    POST /api/devices/{pk}/data/ return 201 if valid; 404 if not owned; 401 if anon.
    """

    queryset = DeviceData.objects.all()
    serializer_class = DeviceDataSerializer
    permission_classes = [IsAuthenticated, IsDataOwner]

    def get_queryset(self):
        # if there is no start_iso and end_iso
        qs = DeviceData.objects.filter(
            device__owner=self.request.user, device_id=self.kwargs['pk']
        )

        # time-interval filter
        start_iso = self.request.GET.get('start', None)
        end_iso = self.request.GET.get('end', None)

        if start_iso or end_iso:
            if not start_iso:
                start_iso = '1980-01-01T00:00:00Z'
            if not end_iso:
                end_iso = '2050-12-31T00:00:00Z'
            start_dt = parse_datetime(start_iso)
            end_dt = parse_datetime(end_iso)

            qs = qs.filter(created_at__range=(start_dt, end_dt))
        return qs

    def perform_create(self, serializer):
        device = get_object_or_404(
            Device, pk=self.kwargs['pk'], owner=self.request.user
        )
        if device.status != Device.DeviceStatus.ONLINE:
            # Raise a 409 Conflict if the device is not online
            raise DeviceStatusConflict()
        serializer.save(device=device)
