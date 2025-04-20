from django.urls import path

from .views import (
    DeviceDataListCreateAPIView,
    DeviceGetUpdateDropAPIView,
    DeviceListCreateAPIView,
)

app_name = 'device'

urlpatterns = [
    path('', DeviceListCreateAPIView.as_view(), name='device-list'),
    path('<int:pk>', DeviceGetUpdateDropAPIView.as_view(), name='device-detail'),
    path('<int:pk>/data', DeviceDataListCreateAPIView.as_view(), name='device-data'),
]
