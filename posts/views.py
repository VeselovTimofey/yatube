from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(1 * 20, key_prefix="index_page")
def index(request):
    posts_list = Post.objects.select_related('group').order_by("-pub_date").all()
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator}
    )


def groups_index(request):
    groups_list = Group.objects.all()
    paginator = Paginator(groups_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "groups_index.html",
        {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts_in_group.order_by("-pub_date").all()
    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    if request.method != "POST":
        form = PostForm()
        return render(request, "new.html", {"form": form})

    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse("index"))

    return render(request, "new.html", {"form": form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    followers = [id[0] for id in author.following.values_list("user")]
    return render(
        request,
        "profile.html",
        {"posts": posts, "author": author,
         "page": page, "paginator": paginator,
         "followers": followers}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    posts = author.posts.all()
    form = CommentForm()
    comments = post.comments.all()
    followers = [id[0] for id in author.following.values_list("user")]
    return render(
        request,
        "post.html",
        {"post": post, "author": author, "posts": posts,
         "comments": comments, "form": form, "followers": followers}
    )


@login_required
def post_edit(request, username, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.user.id == author.id and not form.is_valid():
        return render(
            request,
            "new.html",
            {"form": form, "post": post, "is_edit": is_edit}
        )

    elif request.user.id == author.id and form.is_valid():
        post.save()

    return redirect(reverse(
        "post", kwargs={"username": username, "post_id": post_id})
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("post", username=post.author, post_id=post_id)

    return redirect("post", username=post.author, post_id=post_id)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html",
                  {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("profile", username)
