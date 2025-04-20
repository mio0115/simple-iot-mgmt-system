import factory

from account.tests.factories import UserFactory

from ..models import Device, DeviceData, DeviceLog


class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Device
        django_get_or_create = ('serial_number',)

    name = factory.Sequence(lambda n: f'sensor_{n}')
    device_type = Device.DeviceType.SENSOR
    status = Device.DeviceStatus.ONLINE
    serial_number = factory.Sequence(lambda n: f'{100000 + n}')
    owner = factory.SubFactory(UserFactory)


class DeviceLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceLog

    device = factory.SubFactory(DeviceFactory)
    message = factory.Faker('sentence')


class DeviceDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceData

    device = factory.SubFactory(DeviceFactory)
    data = factory.Faker('sentence')
