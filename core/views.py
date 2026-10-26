
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
from django.db.models import Q, Avg
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
import re

from .models import Project, News, ContactMessage, Comment, Reaction, CommentReaction, EmailVerification, Rating


def home(request):
    projects = Project.objects.all().order_by("-created_at")
    news_list = News.objects.all().order_by("-published_at")
    success = False

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message = request.POST.get("message", "").strip()
        subject = request.POST.get("subject", "").strip()
        contact_method = request.POST.get("contact_method", "").strip()
        additional_fields = [
            value.strip()[:250]
            for value in request.POST.getlist("extra_text_fields[]")
            if value.strip()
        ][:10]
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message,
                extra_fields={
                    "subject": subject,
                    "contact_method": contact_method,
                    "additional_text_fields": additional_fields,
                },
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
            if User.objects.filter(email__iexact=email).exists():
                return render(request, "core/register.html", {
                    "form": form,
                    "registration_error": (
                        "This email address is already registered. "
                        "Please use another email address."
                    ),
                })

            user = form.save(commit=False)
            user.email = email
            user.is_active = False
            user.save()

            verification = EmailVerification.objects.create(
                user=user,
                token=uuid4(),
                expires_at=timezone.now() + timedelta(hours=24),
            )

            verification_url = request.build_absolute_uri(
                reverse("verify_email", args=[str(verification.token)])
            )

            try:
                send_mail(
                    "Verify your SCDFWebsite account",
                    (
                        f"Hello {user.username},\n\n"
                        "Please verify your email address using this link:\n"
                        f"{verification_url}\n\n"
                        "This link expires in 24 hours."
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                return render(request, "core/register.html", {
                    "form": form,
                    "registration_error": (
                        "We could not send the verification email. "
                        "Your account is not active yet. Please contact "
                        "the site administrator for help."
                    ),
                })

            return render(request, "core/register.html", {
                "form": UserCreationForm(),
                "registration_error": (
                    "Registration received! Check your email and click "
                    "the verification link to activate your account."
                ),
            })

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


def verify_email(request, token):
    verification = get_object_or_404(
        EmailVerification,
        token=token,
        is_used=False,
    )

    if verification.expires_at <= timezone.now():
        verification.is_used = True
        verification.save(update_fields=["is_used"])
        return render(request, "core/verify_email.html", {
            "status": "expired",
        })

    user = verification.user
    user.is_active = True
    user.save(update_fields=["is_active"])

    verification.is_used = True
    verification.save(update_fields=["is_used"])

    return render(request, "core/verify_email.html", {
        "status": "success",
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


def _comment_data(comment, user=None):
    reactions = CommentReaction.objects.filter(comment=comment)
    user_reaction = None

    if user is not None and user.is_authenticated:
        user_reaction = reactions.filter(user=user).values_list(
            "reaction", flat=True
        ).first()

    return {
        "id": comment.pk,
        "author": comment.author.username,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        "like_count": reactions.filter(reaction=Reaction.LIKE).count(),
        "dislike_count": reactions.filter(reaction=Reaction.DISLIKE).count(),
        "user_reaction": user_reaction,
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
        "comments": [_comment_data(comment, request.user) for comment in comments],
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


@login_required
@require_POST
def react_to_post(request):
    post_type = request.POST.get("post_type", "").strip()
    post_id = request.POST.get("post_id", "").strip()
    reaction_type = request.POST.get("reaction", "").strip()

    if post_type not in ("news", "project"):
        return JsonResponse(
            {"error": "Post type must be news or project."},
            status=400,
        )

    if not post_id.isdigit() or int(post_id) < 1:
        return JsonResponse(
            {"error": "A valid post ID is required."},
            status=400,
        )

    if reaction_type not in (Reaction.LIKE, Reaction.DISLIKE):
        return JsonResponse(
            {"error": "Reaction must be like or dislike."},
            status=400,
        )

    try:
        post = (
            get_object_or_404(News, pk=int(post_id))
            if post_type == "news"
            else get_object_or_404(Project, pk=int(post_id))
        )
    except Http404:
        return JsonResponse(
            {"error": "The selected post was not found."},
            status=404,
        )

    lookup = {
        "user": request.user,
        post_type: post,
    }
    existing = Reaction.objects.filter(**lookup).first()

    if existing and existing.reaction == reaction_type:
        existing.delete()
        user_reaction = None
    elif existing:
        existing.reaction = reaction_type
        existing.save(update_fields=["reaction", "updated_at"])
        user_reaction = reaction_type
    else:
        Reaction.objects.create(**lookup, reaction=reaction_type)
        user_reaction = reaction_type

    reactions = Reaction.objects.filter(**{post_type: post})

    return JsonResponse({
        "success": True,
        "like_count": reactions.filter(
            reaction=Reaction.LIKE
        ).count(),
        "dislike_count": reactions.filter(
            reaction=Reaction.DISLIKE
        ).count(),
        "user_reaction": user_reaction,
    })

@login_required
@require_GET
def load_reactions(request):
    post_type = request.GET.get("post_type", "").strip()
    post_id = request.GET.get("post_id", "").strip()

    if post_type not in ("news", "project"):
        return JsonResponse(
            {"error": "Post type must be news or project."},
            status=400,
        )

    if not post_id.isdigit() or int(post_id) < 1:
        return JsonResponse(
            {"error": "A valid post ID is required."},
            status=400,
        )

    model = News if post_type == "news" else Project
    post = get_object_or_404(model, pk=int(post_id))
    reactions = Reaction.objects.filter(**{post_type: post})

    own_reaction = reactions.filter(user=request.user).values_list(
        "reaction", flat=True
    ).first()

    return JsonResponse({
        "success": True,
        "like_count": reactions.filter(
            reaction=Reaction.LIKE
        ).count(),
        "dislike_count": reactions.filter(
            reaction=Reaction.DISLIKE
        ).count(),
        "user_reaction": own_reaction,
    })


@login_required
@require_POST
def react_to_comment(request):
    comment_id = request.POST.get("comment_id", "").strip()
    reaction_type = request.POST.get("reaction", "").strip()

    if not comment_id.isdigit() or int(comment_id) < 1:
        return JsonResponse(
            {"error": "A valid comment ID is required."},
            status=400,
        )

    if reaction_type not in (Reaction.LIKE, Reaction.DISLIKE):
        return JsonResponse(
            {"error": "Reaction must be like or dislike."},
            status=400,
        )

    comment = get_object_or_404(Comment, pk=int(comment_id))
    lookup = {"user": request.user, "comment": comment}
    existing = CommentReaction.objects.filter(**lookup).first()

    if existing and existing.reaction == reaction_type:
        existing.delete()
        user_reaction = None
    elif existing:
        existing.reaction = reaction_type
        existing.save(update_fields=["reaction", "updated_at"])
        user_reaction = reaction_type
    else:
        CommentReaction.objects.create(**lookup, reaction=reaction_type)
        user_reaction = reaction_type

    reactions = CommentReaction.objects.filter(comment=comment)

    return JsonResponse({
        "success": True,
        "comment_id": comment.id,
        "like_count": reactions.filter(reaction=Reaction.LIKE).count(),
        "dislike_count": reactions.filter(reaction=Reaction.DISLIKE).count(),
        "user_reaction": user_reaction,
    })



@require_GET
def load_ratings(request):
    post_type = request.GET.get("post_type", "").strip()
    post_id = request.GET.get("post_id", "").strip()

    if post_type not in ("news", "project"):
        return JsonResponse(
            {"error": "Post type must be news or project."},
            status=400,
        )

    if not post_id.isdigit() or int(post_id) < 1:
        return JsonResponse(
            {"error": "A valid post ID is required."},
            status=400,
        )

    model = News if post_type == "news" else Project
    post = get_object_or_404(model, pk=int(post_id))
    ratings = Rating.objects.filter(**{post_type: post})
    average = ratings.aggregate(Avg("score"))["score__avg"]

    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).values_list(
            "score", flat=True
        ).first()

    return JsonResponse({
        "success": True,
        "average_rating": round(average, 1) if average is not None else 0,
        "total_ratings": ratings.count(),
        "user_rating": user_rating,
    })


@login_required
@require_POST
def rate_post(request):
    post_type = request.POST.get("post_type", "").strip()
    post_id = request.POST.get("post_id", "").strip()
    score = request.POST.get("score", "").strip()

    if post_type not in ("news", "project"):
        return JsonResponse(
            {"error": "Post type must be news or project."},
            status=400,
        )

    if not post_id.isdigit() or int(post_id) < 1:
        return JsonResponse(
            {"error": "A valid post ID is required."},
            status=400,
        )

    if score not in ("1", "2", "3", "4", "5"):
        return JsonResponse(
            {"error": "Rating must be between 1 and 5 stars."},
            status=400,
        )

    model = News if post_type == "news" else Project
    post = get_object_or_404(model, pk=int(post_id))
    lookup = {"user": request.user, post_type: post}

    rating, created = Rating.objects.update_or_create(
        **lookup,
        defaults={"score": int(score)},
    )

    ratings = Rating.objects.filter(**{post_type: post})
    average = ratings.aggregate(Avg("score"))["score__avg"]

    return JsonResponse({
        "success": True,
        "created": created,
        "average_rating": round(average, 1) if average is not None else 0,
        "total_ratings": ratings.count(),
        "user_rating": rating.score,
    })

