"""
Define customized permission.
"""

from rest_framework.permissions import BasePermission

from .models import Device


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of a device to view/edit it.
    """

    def has_permission(self, request, view):
        dev_pk = view.kwargs.get('pk')
        return Device.objects.filter(pk=dev_pk, owner=request.user).exists()

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named 'owner'
        return getattr(obj, 'owner', None) == request.user


class IsDataOwner(BasePermission):
    """
    Object-level permission to only allow owners of a device to send data/log to it.
    """

    def has_permission(self, request, view):
        dev_pk = view.kwargs.get('pk')
        return Device.objects.filter(pk=dev_pk, owner=request.user).exists()

    def has_object_permission(self, request, view, obj):
        return obj.device.owner == request.user
