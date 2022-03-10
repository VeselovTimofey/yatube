from django.contrib.auth import get_user_model
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
        cls.unauthorized_client = Client()

    def test_homepage(self):
        response = StaticURLTest.unauthorized_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_personal_page(self):
        response = StaticURLTest.authorizer_client.get(
            reverse('profile', args=['StasBasov'])
        )
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        response = StaticURLTest.authorizer_client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpage(self):
        response = StaticURLTest.unauthorized_client.get(reverse('new_post'))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("new_post")}',
            status_code=302, target_status_code=200
        )

    def test_error_404(self):
        response = StaticURLTest.unauthorized_client.get('/ajdshfwbetg123sg/')
        self.assertEqual(response.status_code, 404)
