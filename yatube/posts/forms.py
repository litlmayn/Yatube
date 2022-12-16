from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {
            'text': 'Пост',
            'group': 'Группа',
            'image': 'Картинка',
        }
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    help_text = 'Форма создания комментария'

    class Meta:
        model = Comment
        labels = {
            'text': 'Текст комментария',
        }
        fields = ('text',)
