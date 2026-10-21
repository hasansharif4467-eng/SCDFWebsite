
from django.shortcuts import render, redirect
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
