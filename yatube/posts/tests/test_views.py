from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.forms import PostForm
from posts.models import Post, Group, Follow, User

AMOUNT_POSTS = 13


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/posts'
        )
        cls.user = User.objects.create_user(username='Stas')
        cls.user_follower = User.objects.create_user(username='Ivan')
        cls.group = Group.objects.create(
            title='Пробная группа',
            slug='test-slug'
        )
        cls.group2 = Group.objects.create(
            title='Пробная группа 2',
            slug='test-slug2'
        )
        cls.post = Post.objects.create(
            text='Пробный пост',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_follower = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_follower.force_login(self.user_follower)

    def test_paginator(self):
        """Paginator работает коректно."""
        self.authorized_client_follower.get(reverse(
            'posts:profile_follow', args=(self.user,)
        ))
        Post.objects.all().delete()
        objs = (
            Post(
                text=f'Test {number_post}',
                author=self.user,
                group=self.group,
            )
            for number_post in range(AMOUNT_POSTS)
        )
        Post.objects.bulk_create(objs)
        number_of_posts_page = (
            ('?page=1', settings.POST_PER_PAGE),
            ('?page=2', (AMOUNT_POSTS - settings.POST_PER_PAGE)),
        )
        page_for_test_paginator = (
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug,)),
            reverse('posts:profile', args=(self.user.username,)),
            reverse('posts:follow_index'),
        )
        for name_page in page_for_test_paginator:
            with self.subTest(name_page=name_page):
                for number_page, number_post in number_of_posts_page:
                    with self.subTest(number_page=number_page):
                        response = self.authorized_client_follower.get(
                            name_page + number_page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']), number_post
                        )

    def for_test_context(self, response, bollin=False):
        if bollin:
            request = response.context.get('post')
        else:
            request = response.context['page_obj'][0]
        self.assertEqual(request.text, self.post.text)
        self.assertEqual(request.author, self.post.author)
        self.assertEqual(request.group, self.post.group)
        self.assertEqual(request.pub_date, self.post.pub_date)
        self.assertEqual(request.image, self.post.image)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        cache.clear()
        response = self.client.get(reverse(
            'posts:index', args=(None)
        ))
        self.for_test_context(response)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.client.get(reverse(
            'posts:group_list', args=(self.group.slug,)
        ))
        self.for_test_context(response)
        expected = response.context['group']
        self.assertEqual(self.group, expected)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.client.get(reverse(
            'posts:profile', args=(self.post.author,)
        ))
        self.for_test_context(response)
        expected = response.context['author']
        self.assertEqual(self.user, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:post_detail', args=(self.post.id,)
        ))
        self.for_test_context(response, True)

    def test_create_edit_show_correct_context(self):
        """Шаблоны post_edit и post_create сформированы с правильно."""
        name_template = (
            ('posts:post_edit', (self.post.id,),),
            ('posts:post_create', None,),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for adress, argument in name_template:
            with self.subTest(adress=adress):
                response = self.authorized_client.post(
                    reverse(adress, args=(argument),))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)

    def post_in_group(self):
        """Пост при создании попадает в правильную группу."""
        response_new_group = self.authorized_client.post(
            reverse('posts:group_list', args=(self.group2.id,),)
        )
        response_old_group = self.authorized_client.post(
            reverse('posts:group_list', args=(self.group.id,),)
        )
        self.assertEqual(len(response_new_group.context['page_obj']), 0)
        self.assertEqual(
            response_old_group.context.get('post').group, self.post.group
        )
        self.assertEqual(len(response_old_group.context['page_obj']), not 0)

    def test_index_cache_context(self):
        """Удаленный пост остается в content до обновления кэша."""
        response_1 = self.client.get(
            reverse('posts:index')
        )
        Post.objects.all().delete()
        response_2 = self.client.get(
            reverse('posts:index')
        )
        cache.clear()
        response_3 = self.client.get(
            reverse('posts:index')
        )
        self.assertEqual(response_1.content, response_2.content)
        self.assertNotEqual(response_1.content, response_3.content)

    def test_follow_user(self):
        """Проверка отписки и подписки на автора."""
        follow_count_do = Follow.objects.count()
        Follow.objects.create(author=self.user, user=self.user_follower)
        follow_count_after = Follow.objects.count()
        self.authorized_client_follower.get(reverse(
            'posts:profile_unfollow', args=(self.user,)
        ))
        author = Follow.objects.all().author
        user = Follow.objects.all().user
        self.assertEqual(author, self.user)
        self.assertEqual(user, self.user_follower)
        self.assertEqual(follow_count_after, (follow_count_do + 1))
        self.assertEqual(Follow.objects.count(), (follow_count_after - 1))

    def test_follower_correct_added(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан.
        """
        Follow.objects.create(author=self.user, user=self.user_follower)
        response = self.authorized_client_follower.get(reverse(
            'posts:follow_index'
        ))
        self.assertIn(self.post, response.context['page_obj'])

    def test_unfollower_correct_added(self):
        """
        Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        response = self.authorized_client_follower.get(reverse(
            'posts:follow_index'
        ))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_two_follow(self):
        """Нельзя подписаться два раза на одного автора."""
        # тест падает, не пойму почему
        Follow.objects.create(author=self.user, user=self.user_follower)
        follow_count = Follow.objects.count()
        Follow.objects.create(author=self.user, user=self.user_follower)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_for_my(self):
        """Нельзя подписаться на самого себя."""
        # тест падает, не пойму почему
        Follow.objects.create(author=self.user, user=self.user)
        self.assertEqual(Follow.objects.count(), 0)
