from django.contrib import admin
from .models import Project, News, ContactMessage


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
