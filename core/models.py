import re

from django.db import models
from django.conf import settings


class EmailVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )
    token = models.UUIDField(unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Email verification for {self.user.username}"


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="news/", blank=True, null=True)
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    extra_fields = models.JSONField(default=dict, blank=True)
    CATEGORY_CHOICES = [
        ("pending", "Pending"),
        ("volunteering", "Volunteering"),
        ("project_inquiry", "Project Inquiry"),
        ("partnership", "Partnership"),
        ("training_inquiry", "Training Inquiry"),
        ("complaint", "Complaint"),
        ("other", "Other / Unclear"),
    ]

    ai_category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="pending",
    )
    corrected_category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        blank=True,
        default="",
    )
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"


class Comment(models.Model):
    author = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="scdf_comments",
    )
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=True,
        null=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=True,
        null=True,
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username}"


class Reaction(models.Model):
    LIKE = "like"
    DISLIKE = "dislike"

    REACTION_CHOICES = [
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    ]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="scdf_reactions",
    )
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="reactions",
        blank=True,
        null=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="reactions",
        blank=True,
        null=True,
    )
    reaction = models.CharField(
        max_length=7,
        choices=REACTION_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "news"],
                name="unique_user_news_reaction",
            ),
            models.UniqueConstraint(
                fields=["user", "project"],
                name="unique_user_project_reaction",
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.reaction}"


class CommentReaction(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="scdf_comment_reactions",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    reaction = models.CharField(
        max_length=7,
        choices=Reaction.REACTION_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comment"],
                name="unique_user_comment_reaction",
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.reaction} on comment {self.comment_id}"


class Rating(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="scdf_ratings",
    )
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="ratings",
        blank=True,
        null=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="ratings",
        blank=True,
        null=True,
    )
    score = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} Star") for i in range(1, 6)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "news"],
                name="unique_user_news_rating",
            ),
            models.UniqueConstraint(
                fields=["user", "project"],
                name="unique_user_project_rating",
            ),
        ]

    def __str__(self):
        target = self.news or self.project
        return f"{self.user.username}: {self.score} stars for {target}"


class Media(models.Model):
    YOUTUBE = "youtube"
    VIDEO = "video"
    AUDIO = "audio"

    MEDIA_TYPES = [
        (YOUTUBE, "YouTube"),
        (VIDEO, "Video"),
        (AUDIO, "Audio"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        default=YOUTUBE,
    )
    youtube_url = models.URLField(blank=True)
    media_file = models.FileField(
        upload_to="media/files/",
        blank=True,
        null=True,
    )
    thumbnail = models.ImageField(
        upload_to="media/thumbnails/",
        blank=True,
        null=True,
    )
    published_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    @property
    def youtube_embed_url(self):
        if not self.youtube_url:
            return ""

        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(self.youtube_url)
        video_id = ""

        if parsed.hostname in ("youtu.be", "www.youtu.be"):
            video_id = parsed.path.strip("/").split("/")[0]

        elif parsed.hostname in (
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
        ):
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]

            elif parsed.path.startswith("/embed/"):
                video_id = parsed.path.split("/embed/")[1].split("/")[0]

            elif parsed.path.startswith("/shorts/"):
                video_id = parsed.path.split("/shorts/")[1].split("/")[0]

        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return ""

        return f"https://www.youtube-nocookie.com/embed/{video_id}"

    def __str__(self):
        return self.title