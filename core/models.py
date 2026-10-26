
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
