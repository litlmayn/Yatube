from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, Comment, User


class TaskFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Bob')
        cls.user_follow = User.objects.create_user(username='Ivan')
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.autorized_client = Client()
        self.autorized_client_follow = Client()
        self.autorized_client.force_login(self.user)
        self.autorized_client_follow.force_login(self.user)

    def test_creat_post(self):
        """Проверка создания поста."""
        Post.objects.all().delete()
        post_count = Post.objects.count()
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
            content_type='image/posts',
        )
        form_data = {
            'text': 'Test post 2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.autorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(self.user.username,)
        )
        )
        self.assertEqual(Post.objects.count(), (post_count + 1))
        self.assertEqual(Post.objects.first().text, form_data['text'])
        self.assertEqual(Post.objects.get().author, self.user)
        self.assertEqual(Post.objects.get().group.id, form_data['group'])

    def test_edit_post(self):
        """Проверка, что пост редактируется в базе данных"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'New text',
            'group': self.group2.id,
        }
        response = self.autorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        response_old_group = self.autorized_client.post(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(response_old_group.status_code, HTTPStatus.OK)
        self.assertEqual(len(response_old_group.context['page_obj']), 0)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.first().text, form_data['text'])
        self.assertEqual(Post.objects.get().group.id, form_data['group'])
        self.assertEqual(Post.objects.get().author, self.post.author)

    def test_guest_client_creat_post(self):
        """Неавторизированный клиент не может создать пост."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Quest client',
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)

    def test_guest_client_creat_comment(self):
        """Неавторизированный клиент не может создать комментарий."""
        post_comment = Comment.objects.count()
        form_data = {
            'text': 'Comment quest client',
        }
        response = self.client.post(
            reverse('posts:post_detail', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), post_comment)

    def test_create_comment(self):
        """Проверка создания комментария."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Test comment',
        }
        self.autorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), (comment_count + 1))
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(Post.objects.get().author, self.user)
        self.assertEqual(Post.objects.get(), self.post)
