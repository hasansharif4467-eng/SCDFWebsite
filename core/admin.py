
from django.contrib import admin
from .models import Project, News, ContactMessage, Comment, EmailVerification


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "is_used")
    search_fields = ("user__username", "user__email")
    list_filter = ("is_used", "created_at")
    readonly_fields = ("token", "created_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "created_at")
    search_fields = ("title", "description", "location")
    list_filter = ("created_at",)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at")
    search_fields = ("title", "content")
    list_filter = ("published_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "phone", "message")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "news", "project", "created_at")
    search_fields = ("content", "author__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "news", "project", "score", "created_at", "updated_at")
    search_fields = ("user__username", "news__title", "project__title")
    list_filter = ("score", "created_at")
    readonly_fields = ("created_at", "updated_at")
