
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import Http404
from django.views.decorators.http import require_POST, require_GET
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
import re

from .models import Project, News, ContactMessage, Comment


def home(request):
    projects = Project.objects.all().order_by("-created_at")
    news_list = News.objects.all().order_by("-published_at")
    success = False

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message,
            )
            return redirect("/?contact=success#contact")

    if request.GET.get("contact") == "success":
        success = True

    context = {
        "projects": projects,
        "news_list": news_list,
        "contact_success": success,
    }
    return render(request, "core/index.html", context)


def check_username(request):
    username = request.GET.get("username", "").strip()

    if not username:
        return JsonResponse({
            "available": False,
            "message": "Username is required.",
        })

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
        return JsonResponse({
            "available": False,
            "message": (
                "Use letters, numbers, underscore, hyphen or dot only."
            ),
        })

    try:
        UserCreationForm().fields["username"].clean(username)
    except ValidationError:
        return JsonResponse({
            "available": False,
            "message": "Invalid username.",
        })

    exists = User.objects.filter(username__iexact=username).exists()

    return JsonResponse({
        "available": not exists,
        "message": (
            "Username is already taken."
            if exists
            else "Username is available."
        ),
    })


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        try:
            email = forms.EmailField().clean(
                request.POST.get("email", "").strip()
            )
        except ValidationError:
            email = ""

        if form.is_valid() and email:
            user = form.save(commit=False)
            user.email = email
            user.save()
            login(request, user)
            return redirect("home")

        return render(request, "core/register.html", {
            "form": form,
            "registration_error": (
                "Please enter a valid email and check your username "
                "and password details."
            ),
        })

    return render(request, "core/register.html", {
        "form": UserCreationForm(),
    })


def _get_post_for_comment(request):
    """Return the selected News or Project, or None for invalid input."""
    post_type = request.POST.get("post_type", "").strip()
    post_id = request.POST.get("post_id", "").strip()

    if not post_id.isdigit() or int(post_id) < 1:
        return None, None

    if post_type == "news":
        return "news", get_object_or_404(News, pk=int(post_id))

    if post_type == "project":
        return "project", get_object_or_404(Project, pk=int(post_id))

    return None, None


def _comment_data(comment):
    return {
        "id": comment.pk,
        "author": comment.author.username,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
    }


@require_GET
def load_comments(request):
    post_type = request.GET.get("post_type", "").strip()
    post_id = request.GET.get("post_id", "").strip()

    if not post_id.isdigit() or int(post_id) < 1:
        return JsonResponse(
            {"error": "A valid post ID is required."},
            status=400,
        )

    try:
        if post_type == "news":
            post = get_object_or_404(News, pk=int(post_id))
            comments = post.comments.select_related("author").all()
        elif post_type == "project":
            post = get_object_or_404(Project, pk=int(post_id))
            comments = post.comments.select_related("author").all()
        else:
            return JsonResponse(
                {"error": "Post type must be news or project."},
                status=400,
            )
    except Http404:
        return JsonResponse(
            {"error": "The selected post was not found."},
            status=404,
        )
    return JsonResponse({
        "comments": [_comment_data(comment) for comment in comments],
    })


@login_required
@require_POST
def add_comment(request):
    try:
        post_type, post = _get_post_for_comment(request)
    except Http404:
        return JsonResponse(
            {"error": "The selected post was not found."},
            status=404,
        )

    if post is None:
        return JsonResponse(
            {"error": "Select a valid News or Project post."},
            status=400,
        )

    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse(
            {"error": "Comment cannot be empty."},
            status=400,
        )

    if len(content) > 2000:
        return JsonResponse(
            {"error": "Comment must be 2000 characters or fewer."},
            status=400,
        )

    comment_data = {
        "author": request.user,
        "content": content,
    }

    if post_type == "news":
        comment_data["news"] = post
    else:
        comment_data["project"] = post

    comment = Comment.objects.create(**comment_data)

    return JsonResponse({
        "success": True,
        "comment": _comment_data(comment),
    }, status=201)
