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
    class Meta:
        model = Comment
        help_texts = {
            'text': 'Текст комментария',
        }
        fields = ('text',)
