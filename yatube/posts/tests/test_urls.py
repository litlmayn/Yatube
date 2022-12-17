from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pip')
        cls.user2 = User.objects.create_user(username='Pup')
        cls.group = Group.objects.create(
            title='Пробная группа',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Пробный пост',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)
        self.urls_test_pakeg = (
            ('posts:index', None,),
            ('posts:group_list', (self.group.slug,),),
            ('posts:profile', (self.user.username,),),
            ('posts:post_detail', (self.post.id,),),
            ('posts:post_edit', (self.post.id,),),
            ('posts:post_create', None,),
            ('posts:add_comment', (self.post.id,),),
            ('posts:follow_index', None,),
            ('posts:profile_follow', (self.user.username,),),
            ('posts:profile_unfollow', (self.user.username,),),
        )

    def test_urls_correct_template(self):
        """Шаблоны работаю корректно."""
        templates_url_name = (
            ('posts:index', None,
             'posts/index.html'),
            ('posts:group_list', (self.group.slug,),
             'posts/group_list.html'),
            ('posts:profile', (self.user.username,),
             'posts/profile.html'),
            ('posts:post_detail', (self.post.id,),
             'posts/post_detail.html'),
            ('posts:post_create', None,
             'posts/create_post.html'),
            ('posts:follow_index', None,
             'posts/follow.html'),
        )
        for address, arguments, template in templates_url_name:
            with self.subTest(address=address):
                response = self.authorized_client.post(reverse(address, args=(
                    arguments)))
                self.assertTemplateUsed(response, template)

    def test_urls_conformity_reverse(self):
        """Url открывает нужный адресс."""
        templates_url_name = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
             f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.id,),
             f'/posts/{self.post.id}/'),
            ('posts:post_edit', (self.post.id,),
             f'/posts/{self.post.id}/edit/'),
            ('posts:post_create', None, '/create/'),
            ('posts:add_comment', (self.post.id,),
             f'/posts/{self.post.id}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow', (self.user.username,),
             f'/profile/{self.user.username}/follow/'),
            ('posts:profile_unfollow', (self.user.username,),
             f'/profile/{self.user.username}/unfollow/'),
        )
        for address, argument, url in templates_url_name:
            with self.subTest(address=address):
                self.assertEqual(reverse(address, args=(argument)), url)

    def test_url_nonexists(self):
        """Проверка доступности несуществующего адреса."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_unauth_client(self):
        """Проверка urls неавторезированным клиентом."""
        reverse_login = reverse('users:login')
        exceptions = (
            ('posts:post_create'),
            ('posts:post_edit'),
            ('posts:follow_index'),
            ('posts:profile_follow'),
            ('posts:profile_unfollow'),
            ('posts:add_comment'),
        )
        for name, argument in self.urls_test_pakeg:
            with self.subTest(name=name):
                if name in exceptions:
                    reverse_name = reverse(name, args=(argument))
                    response = self.client.post(
                        reverse(name, args=(argument)), follow=True)
                    self.assertRedirects(
                        response,
                        (f'{reverse_login}?next={reverse_name}')
                    )
                else:
                    response = self.client.post(reverse(name, args=(argument)))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_auth_client(self):
        """Проверка urls авторизированным клиентом."""
        for name, argument in self.urls_test_pakeg:
            with self.subTest(name=name):
                if name == 'posts:post_edit' or name == 'posts:add_comment':
                    response = self.authorized_client2.post(reverse(
                        name, args=(argument)), follow=True)
                    self.assertRedirects(
                        response,
                        (reverse('posts:post_detail', args=(self.post.id,), ))
                    )
                elif name in ('posts:profile_follow',
                              'posts:profile_unfollow'):
                    response = self.authorized_client2.post(reverse(
                        name, args=(argument)), follow=True)
                    self.assertRedirects(
                        response,
                        (reverse('posts:profile', args=(self.user,),))
                    )

                else:
                    response = self.authorized_client2.post(
                        reverse(name, args=(argument)), )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_autor(self):
        """Проверка urls автором."""
        for name, argument in self.urls_test_pakeg:
            with self.subTest(name=name):
                if name == 'posts:add_comment':
                    response = self.authorized_client2.post(reverse(
                        name, args=(argument)), follow=True)
                    self.assertRedirects(
                        response,
                        (reverse('posts:post_detail', args=(self.post.id,), ))
                    )
                elif name == 'posts:profile_follow':
                    response = self.authorized_client2.post(reverse(
                        name, args=(argument)), follow=True)
                    self.assertRedirects(
                        response,
                        (reverse('posts:profile', args=(self.user,)))
                    )
                elif name == 'posts:profile_unfollow':
                    response = self.authorized_client.post(reverse(
                        name, args=(argument)), follow=True)
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )
                else:
                    response = response = self.authorized_client.post(
                        reverse(name, args=(argument))
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_error(self):
        """При ошибке 404 открывается кастомный шаблон."""
        response = self.client.post(reverse('posts:profile', args=('pupis',)))
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
