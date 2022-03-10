from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user2 = User.objects.create_user(username='ProstoStas')
        cls.authorizer_client = Client()
        cls.authorizer_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(title='test',
                                         description='test',
                                         slug='test')

    def test_user_can_subscribe(self):
        self.authorizer_client.force_login(self.user)
        current_following_count = self.user.following.count()
        response_follow = self.authorizer_client.get(
            reverse('profile_follow', kwargs={'username': self.user2})
        )
        self.assertRedirects(response_follow,
                             reverse('profile',
                                     kwargs={'username': self.user2}))
        self.assertEqual(Follow.objects.count(), current_following_count + 1)

    def test_user_can_unsubscribe(self):
        self.authorizer_client.force_login(self.user)
        self.authorizer_client.get(reverse('profile_follow',
                                           kwargs={'username': self.user2}))
        current_following_count = self.user.following.count()
        response_unfollow = self.authorizer_client.get(
            reverse('profile_unfollow', kwargs={'username': self.user2})
        )
        self.assertRedirects(response_unfollow,
                             reverse('profile',
                                     kwargs={'username': self.user2}))
        self.assertEqual(Follow.objects.count(), current_following_count)

    def test_subscribe_post(self):
        self.authorizer_client.get(reverse('profile_follow',
                                           kwargs={'username': self.user2}))
        self.authorizer_client.force_login(self.user2)
        self.authorizer_client.post(reverse('new_post'),
                                    {'text': 'Это текст публикации'},
                                    follow=True)
        post_check = Post.objects.first()
        self.authorizer_client.force_login(self.user)
        response = self.authorizer_client.get(reverse('follow_index'),
                                              follow=True)
        response = response.context['page'][0].text
        self.assertEqual(response, post_check.text)
