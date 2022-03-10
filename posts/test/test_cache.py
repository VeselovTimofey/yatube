from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorizer_client = Client()
        cls.authorizer_client.force_login(cls.user)

    def test_cache_after_time(self):
        response_old = self.authorizer_client.get(reverse('index'))
        StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'Это текст публикации'},
            follow=True
        )
        response_new = self.authorizer_client.get(reverse('index'))
        self.assertEqual(response_old.content, response_new.content)
        cache.clear()
        response_newest = self.authorizer_client.get(reverse('index'))
        self.assertNotEqual(response_old.content, response_newest.content)
