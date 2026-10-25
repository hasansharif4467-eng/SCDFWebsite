
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import ContactMessage, News, Project, Comment, Reaction, EmailVerification


class HomeViewTests(TestCase):
    def test_homepage_returns_200(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")

    def test_contact_form_saves_valid_message(self):
        response = self.client.post(
            reverse("home"),
            {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "01800000000",
                "message": "Testing contact form",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(
            ContactMessage.objects.first().name,
            "Test User",
        )

    def test_contact_form_rejects_missing_required_fields(self):
        response = self.client.post(
            reverse("home"),
            {
                "name": "",
                "email": "test@example.com",
                "message": "Testing contact form",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)


class UsernameCheckViewTests(TestCase):
    def test_available_username(self):
        response = self.client.get(
            reverse("check_username"),
            {"username": "new_test_user"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "available": True,
                "message": "Username is available.",
            },
        )

    def test_existing_username_is_unavailable(self):
        User.objects.create_user(
            username="ExistingUser",
            password="TestPass123!",
        )

        response = self.client.get(
            reverse("check_username"),
            {"username": "existinguser"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "available": False,
                "message": "Username is already taken.",
            },
        )

    def test_empty_username_is_rejected(self):
        response = self.client.get(
            reverse("check_username"),
            {"username": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["available"])

    def test_invalid_username_characters_are_rejected(self):
        response = self.client.get(
            reverse("check_username"),
            {"username": "bad username!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["available"])

from .models import News, Project, Comment


class CommentViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="comment_tester",
            password="TestPass123!",
        )
        self.news = News.objects.create(
            title="Test News",
            content="News content for testing.",
        )
        self.project = Project.objects.create(
            title="Test Project",
            description="Project description for testing.",
        )

    def test_load_news_comments_returns_200(self):
        response = self.client.get(
            reverse("load_comments"),
            {"post_type": "news", "post_id": self.news.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["comments"], [])

    def test_load_project_comments_returns_200(self):
        response = self.client.get(
            reverse("load_comments"),
            {"post_type": "project", "post_id": self.project.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["comments"], [])

    def test_load_comments_rejects_invalid_post_type(self):
        response = self.client.get(
            reverse("load_comments"),
            {"post_type": "invalid", "post_id": self.news.pk},
        )
        self.assertEqual(response.status_code, 400)

    def test_load_comments_returns_404_for_missing_post(self):
        response = self.client.get(
            reverse("load_comments"),
            {"post_type": "news", "post_id": 999999},
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_add_comment(self):
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "content": "Anonymous comment",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authenticated_user_can_comment_on_news(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "content": "A valid news comment",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().news, self.news)

    def test_authenticated_user_can_comment_on_project(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "project",
                "post_id": self.project.pk,
                "content": "A valid project comment",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().project, self.project)

    def test_empty_comment_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "content": "   ",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_over_2000_characters_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "content": "x" * 2001,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_invalid_post_id_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": "invalid",
                "content": "Test comment",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_missing_post_returns_404_when_adding_comment(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_comment"),
            {
                "post_type": "news",
                "post_id": 999999,
                "content": "Test comment",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)
class LoginLogoutSessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="session_tester",
            password="TestPass123!",
        )

    def test_login_creates_authenticated_session(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "session_tester",
                "password": "TestPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.client.session.get("_auth_user_id")
        )

    def test_logout_clears_authenticated_session(self):
        self.client.force_login(self.user)
        self.assertTrue(
            self.client.session.get("_auth_user_id")
        )

        response = self.client.post(reverse("logout"))

        self.assertEqual(response.status_code, 302)
        self.assertIsNone(
            self.client.session.get("_auth_user_id")
        )

class ReactionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reaction_tester",
            password="TestPass123!",
        )
        self.news = News.objects.create(
            title="Reaction Test News",
            content="Testing reactions.",
        )
        self.project = Project.objects.create(
            title="Reaction Test Project",
            description="Testing project reactions.",
        )

    def test_anonymous_user_cannot_react(self):
        response = self.client.post(
            reverse("react_to_post"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "reaction": "like",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_user_can_like_news(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("react_to_post"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "reaction": "like",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["like_count"], 1)
        self.assertEqual(response.json()["dislike_count"], 0)
        self.assertEqual(response.json()["user_reaction"], "like")

    def test_user_can_change_like_to_dislike(self):
        self.client.force_login(self.user)
        url = reverse("react_to_post")
        payload = {
            "post_type": "news",
            "post_id": self.news.pk,
            "reaction": "like",
        }
        self.client.post(url, payload)
        payload["reaction"] = "dislike"
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["like_count"], 0)
        self.assertEqual(response.json()["dislike_count"], 1)
        self.assertEqual(response.json()["user_reaction"], "dislike")
        self.assertEqual(Reaction.objects.count(), 1)

    def test_repeating_same_reaction_removes_it(self):
        self.client.force_login(self.user)
        url = reverse("react_to_post")
        payload = {
            "post_type": "project",
            "post_id": self.project.pk,
            "reaction": "like",
        }
        self.client.post(url, payload)
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["like_count"], 0)
        self.assertIsNone(response.json()["user_reaction"])
        self.assertEqual(Reaction.objects.count(), 0)

    def test_invalid_reaction_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("react_to_post"),
            {
                "post_type": "news",
                "post_id": self.news.pk,
                "reaction": "love",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Reaction.objects.count(), 0)



class EmailVerificationTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        from uuid import uuid4

        self.email = "verification@example.com"
        self.user = User.objects.create_user(
            username="verification_user",
            email=self.email,
            password="TestPass123!",
            is_active=False,
        )
        self.verification = EmailVerification.objects.create(
            user=self.user,
            token=uuid4(),
            expires_at=timezone.now() + timedelta(hours=24),
        )

    def test_valid_token_activates_account(self):
        response = self.client.get(
            reverse("verify_email", args=[self.verification.token])
        )

        self.user.refresh_from_db()
        self.verification.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.verification.is_used)
        self.assertContains(response, "Email Verified!")

    def test_expired_token_does_not_activate_account(self):
        from datetime import timedelta
        from django.utils import timezone

        self.verification.expires_at = timezone.now() - timedelta(minutes=1)
        self.verification.save(update_fields=["expires_at"])

        response = self.client.get(
            reverse("verify_email", args=[self.verification.token])
        )

        self.user.refresh_from_db()
        self.verification.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.verification.is_used)
        self.assertContains(response, "Verification Link Expired")

    def test_used_token_cannot_be_reused(self):
        self.verification.is_used = True
        self.verification.save(update_fields=["is_used"])

        response = self.client.get(
            reverse("verify_email", args=[self.verification.token])
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.user.is_active)

    def test_invalid_token_returns_404(self):
        from uuid import uuid4

        response = self.client.get(
            reverse("verify_email", args=[uuid4()])
        )

        self.assertEqual(response.status_code, 404)

    def test_registration_sends_verification_email_without_login(self):
        from django.core import mail
        from django.test import override_settings

        with override_settings(ALLOWED_HOSTS=["testserver"]):
            response = self.client.post(
                reverse("register"),
                {
                    "username": "new_verification_user",
                    "email": "new-verification@example.com",
                    "password1": "StrongPass123!Secure",
                    "password2": "StrongPass123!Secure",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(username="new_verification_user")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(
            EmailVerification.objects.filter(user=user).exists()
        )
        self.assertContains(response, "Check your email")

    def test_registration_rejects_duplicate_email(self):
        from django.test import override_settings

        User.objects.create_user(
            username="existing_email_user",
            email="duplicate@example.com",
            password="TestPass123!",
        )

        with override_settings(ALLOWED_HOSTS=["testserver"]):
            response = self.client.post(
                reverse("register"),
                {
                    "username": "duplicate_email_user",
                    "email": "DUPLICATE@example.com",
                    "password1": "StrongPass123!Secure",
                    "password2": "StrongPass123!Secure",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="duplicate_email_user").exists()
        )
        self.assertContains(response, "already registered")
