from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

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

    def test_new_post(self):
        response = StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'Это текст публикации', 'id': 1},
            follow=True
        )
        post = get_object_or_404(Post, pk=1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Это текст публикации' in post.text)

    def test_unauthorized_post(self):
        response = StaticURLTest.unauthorized_client.post(
            reverse('new_post'),
            {'text': 'Это текст публикации', 'id': 1},
            follow=True
        )
        try:
            post = Post.objects.get(pk=1)
        except Post.DoesNotExist:
            post = None
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("new_post")}',
            status_code=302, target_status_code=200
        )
        self.assertEqual(post, None)

    def urls_check(self, text):
        urls = [reverse('index'),
                reverse('profile', args=['StasBasov']),
                reverse('post', args=[self.user, 1])]
        cache.clear()
        for url in urls:
            response_authorized = self.authorizer_client.get(url)
            self.assertContains(response_authorized, text=text)

    def test_show_post(self):
        StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'TestText'},
            follow=True
        )
        self.urls_check(text='TestText')

    def test_show_edit(self):
        StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'NewText'},
            follow=True
        )

        post = Post.objects.get(author=self.user)
        StaticURLTest.authorizer_client.post(
            reverse('post_edit', args=[self.user, post.pk]),
            {'text': 'TestText'},
            follow=True
        )
        self.urls_check(text='TestText')

    def test_post_image(self):
        urls = [reverse('index'),
                reverse('profile', args=['StasBasov']),
                reverse('post', args=[self.user, 1])]
        img = SimpleUploadedFile(
            name='test.png',
            content=open('media/test_image/test.jpg', 'rb').read(),
            content_type='image/jpg'
        )
        post = self.authorizer_client.post(
            reverse('new_post'),
            {'author': self.user,
             'group': self.group.pk,
             'text': 'Пост с картинкой',
             'image': img},
            follow=True
        )
        cache.clear()
        for url in urls:
            response = StaticURLTest.authorizer_client.get(url)
            self.assertContains(response, '<img')

    def test_no_image(self):
        img = SimpleUploadedFile(
            name='test.txt',
            content=open('media/test_image/test.txt', 'rb').read(),
            content_type='image/txt'
        )
        self.authorizer_client.post(
            reverse('new_post'),
            {'author': self.user,
             'text': 'Пост с картинкой',
             'image': img,
             'id': 1},
            follow=True
        )
        try:
            post = Post.objects.get(pk=1)
        except Post.DoesNotExist:
            post = None
        self.assertEqual(post, None)
