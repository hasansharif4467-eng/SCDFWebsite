from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django import forms
from django.core.exceptions import ValidationError
import re

from .models import Project, News, ContactMessage


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
            "message": "Username is required."
        })

    # Allow English letters, numbers, underscore, hyphen and dot only.
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
        return JsonResponse({
            "available": False,
            "message": (
                "Use letters, numbers, underscore, hyphen or dot only."
            )
        })

    # Enforce Django's username field validation.
    try:
        UserCreationForm().fields["username"].clean(username)
    except ValidationError:
        return JsonResponse({
            "available": False,
            "message": "Invalid username."
        })

    exists = User.objects.filter(username__iexact=username).exists()

    return JsonResponse({
        "available": not exists,
        "message": (
            "Username is already taken."
            if exists
            else "Username is available."
        )
    })


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        # Validate the email on the server.
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
            )
        })

    return render(request, "core/register.html", {
        "form": UserCreationForm()
    })