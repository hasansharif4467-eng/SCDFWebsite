from django.contrib import admin
from .models import Project, News


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