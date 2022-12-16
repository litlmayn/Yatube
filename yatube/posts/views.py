from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .utils import get_paginator
from .forms import PostForm, CommentForm
from .models import Group, Post, Follow, User


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.posts.select_related('group').all()
    page_obj = get_paginator(request, post)
    following = False
    followers = request.user
    if followers.is_authenticated and followers.follower.filter(author=author):
        following = True
    context = {
        'following': following,
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'form': form,
        'comment': post.comments.all(),
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author').all()
    page_obj = get_paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    page_obj = get_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author_id = request.user.id
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Если делаю выборку по автору вылетает 404
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid:
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follower = request.user
    # select_related('author') - выдает все записи
    posts_list = Post.objects.filter(author__following__user=follower)
    page_obj = get_paginator(request, posts_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = request.user
    author = get_object_or_404(User, username=username)
    if follower != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    # сделал как ты сказал
    # 'get_object_or_404(Follow, author__username=username)',
    # в итоге 500 ошибку выдает
    author = get_object_or_404(User, username=username)
    follow = request.user.follower.filter(author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:follow_index')
