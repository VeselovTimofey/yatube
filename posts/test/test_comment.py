from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Post

User = get_user_model()


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorizer_client = Client()
        cls.authorizer_client.force_login(cls.user)
        cls.unauthorized_client = Client()

    def test_unauthorized_comment(self):
        self.authorizer_client.force_login(self.user)
        StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'Это текст публикации'},
            follow=True
        )
        post = get_object_or_404(Post, author=self.user)
        self.unauthorized_client.get(
            reverse('add_comment', args=[self.user, post.pk]),
            {'text': 'No'}
        )
        try:
            commit = Comment.objects.get(post_id=post.pk)
        except Comment.DoesNotExist:
            commit = None
        self.assertEqual(commit, None)
