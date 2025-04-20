import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'user_{n}@example.com')
    name = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'test1234')
