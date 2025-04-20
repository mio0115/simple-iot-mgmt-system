import factory

from account.tests.factories import UserFactory

from ..models import DeviceGroup


class DeviceGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceGroup

    name = factory.Sequence(lambda n: f'group_{n}')
    description = factory.Faker('sentence')
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def devices(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for device in extracted:
                self.devices.add(device)
