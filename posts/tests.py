from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

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

    def test_homepage(self):
        response = StaticURLTest.unauthorized_client.get(reverse('index'))
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

    def test_new_post(self):
        response = StaticURLTest.authorizer_client.post(
            reverse('new_post'),
            {'text': 'Это текст публикации', 'id': 1},
            follow=True
        )
        post = get_object_or_404(Post, pk=1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Это текст публикации' in post.text)

    def test_personal_page(self):
        response = StaticURLTest.authorizer_client.get(
            reverse('profile', args=['StasBasov'])
        )
        self.assertEqual(response.status_code, 200)

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

    def test_error_404(self):
        response = StaticURLTest.unauthorized_client.get('/ajdshfwbetg123sg/')
        self.assertEqual(response.status_code, 404)

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

    def test_user_can_subscribe(self):
        self.authorizer_client.force_login(self.user)
        current_following_count = self.user.following.count()
        response_follow = self.authorizer_client.get(
            reverse('profile_follow', kwargs={'username': self.user2})
        )
        self.assertRedirects(response_follow, reverse('profile',
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
                             reverse('profile', kwargs={'username': self.user2}))
        self.assertEqual(Follow.objects.count(), current_following_count)

    def test_subscribe_post(self):
        self.authorizer_client.get(reverse('profile_follow',
                                           kwargs={'username': self.user2}))
        self.authorizer_client.force_login(self.user2)
        self.authorizer_client.post(reverse('new_post'),
                                    {'text': 'Это текст публикации'}, follow=True)
        post_check = Post.objects.first()
        self.authorizer_client.force_login(self.user)
        response = self.authorizer_client.get(reverse('follow_index'),
                                              follow=True)
        response = response.context['page'][0].text
        self.assertEqual(response, post_check.text)

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
