from unittest.mock import patch
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Article, CustomUser, Newsletter, Publisher


class NewsApplicationAPITests(APITestCase):
    def setUp(self):
        # 1. Create Users for each role
        self.journalist = CustomUser.objects.create_user(
            username="jane_journalist",
            email="jane@news.com",
            password="Password123!",
            role=CustomUser.Role.JOURNALIST,
        )
        self.journalist_token = Token.objects.create(user=self.journalist)

        self.editor = CustomUser.objects.create_user(
            username="edward_editor",
            email="edward@news.com",
            password="Password123!",
            role=CustomUser.Role.EDITOR,
        )
        self.editor_token = Token.objects.create(user=self.editor)

        self.reader = CustomUser.objects.create_user(
            username="rachel_reader",
            email="rachel@reader.com",
            password="Password123!",
            role=CustomUser.Role.READER,
        )
        self.reader_token = Token.objects.create(user=self.reader)

        # 2. Create Publishers
        self.publisher_tech = Publisher.objects.create(
            name="Tech Dispatch", description="Tech news and insights."
        )
        self.publisher_science = Publisher.objects.create(
            name="Science Weekly", description="Science discoveries."
        )

        # 3. Establish Reader Subscriptions (Subscribed to publisher_tech and
        # journalist)
        self.reader.subscribed_publishers.add(self.publisher_tech)
        self.reader.subscribed_journalists.add(self.journalist)

        # 4. Seed sample articles
        # Subscribed article 1 (Matching journalist author)
        self.article_sub1 = Article.objects.create(
            title="AI Advances 2026",
            content="Neural network progress in 2026.",
            author=self.journalist,
            approved=True,
        )

        # Subscribed article 2 (Matching publisher)
        self.article_sub2 = Article.objects.create(
            title="Quantum Compute Breakthrough",
            content="New quantum qubit milestones.",
            author=self.journalist,
            publisher=self.publisher_tech,
            approved=True,
        )

        # Unsubscribed article (Different publisher)
        self.article_unsub = Article.objects.create(
            title="Astronomy Deep Field",
            content="Deep space planetary imaging.",
            author=self.journalist,
            publisher=self.publisher_science,
            approved=True,
        )

        # Pending article (Not approved yet)
        self.article_pending = Article.objects.create(
            title="Pending Draft Article",
            content="This draft is not approved.",
            author=self.journalist,
            approved=False,
        )

    # ========================================================
    # 1. AUTHENTICATION & ROLE ACCESS
    # ========================================================
    def test_unauthenticated_requests_blocked(self):
        """Unauthenticated requests cannot access protected article
        endpoints."""
        url = reverse("article-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_auth_token(self):
        """Users can exchange valid credentials for an auth token."""
        url = reverse("api_token")
        payload = {"username": "jane_journalist", "password": "Password123!"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    # ========================================================
    # 2. ARTICLE RETRIEVAL & SUBSCRIPTION FILTERING
    # ========================================================
    def test_public_articles_feed_only_returns_approved(self):
        """Readers can only see approved articles on the public feed."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.reader_token.key}"
        )
        url = reverse("article-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        titles = [a["title"] for a in response.data]
        self.assertIn(self.article_sub1.title, titles)
        self.assertIn(self.article_sub2.title, titles)
        self.assertIn(self.article_unsub.title, titles)
        self.assertNotIn(self.article_pending.title, titles)

    def test_reader_subscribed_feed_filtering(self):
        """Reader subscribed endpoint returns only content matching
        subscriptions."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.reader_token.key}"
        )
        url = reverse("article-subscribed")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article_ids = [a["id"] for a in response.data]
        self.assertIn(self.article_sub1.id, article_ids)
        self.assertIn(self.article_sub2.id, article_ids)
        # Verify article under science publisher (not subscribed) is excluded
        self.reader.subscribed_journalists.remove(self.journalist)
        response_filtered = self.client.get(url)
        filtered_ids = [a["id"] for a in response_filtered.data]
        self.assertIn(self.article_sub2.id, filtered_ids)
        self.assertNotIn(self.article_unsub.id, filtered_ids)

    # ========================================================
    # 3. ARTICLE CREATION (ROLE AUTHORIZATION)
    # ========================================================
    def test_journalist_can_create_article(self):
        """Journalists can successfully submit new articles."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.journalist_token.key}"
        )
        url = reverse("article-list")
        payload = {
            "title": "Autonomous Code Generation",
            "content": "How agents write code in 2026.",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["author_username"], self.journalist.username
        )
        # Articles must default to unapproved upon submission
        self.assertFalse(response.data["approved"])

    def test_reader_cannot_create_article(self):
        """Readers receive 403 Forbidden when attempting to POST articles."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.reader_token.key}"
        )
        url = reverse("article-list")
        payload = {
            "title": "Spam Title",
            "content": "Unauthorized post attempt.",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ========================================================
    # 4. ARTICLE UPDATE & DELETION (EDITOR PRIVILEGES)
    # ========================================================
    def test_editor_can_update_and_delete_article(self):
        """Editors can update and delete any journalist article."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.editor_token.key}"
        )
        detail_url = reverse(
            "article-detail", kwargs={"pk": self.article_sub1.pk}
        )

        # Update
        patch_response = self.client.patch(
            detail_url, {"title": "Updated Title by Editor"}
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            patch_response.data["title"], "Updated Title by Editor"
        )

        # Delete
        delete_response = self.client.delete(detail_url)
        self.assertEqual(
            delete_response.status_code, status.HTTP_204_NO_CONTENT
        )
        self.assertFalse(
            Article.objects.filter(pk=self.article_sub1.pk).exists()
        )

    def test_reader_cannot_delete_article(self):
        """Readers receive 403 Forbidden when attempting to DELETE articles."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.reader_token.key}"
        )
        detail_url = reverse(
            "article-detail", kwargs={"pk": self.article_sub1.pk}
        )
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ========================================================
    # 5. SIGNAL AUTOMATION & MOCKING (EMAIL & WEBHOOK)
    # ========================================================
    @patch("requests.post")
    def test_approval_signal_triggers_email_and_webhook_mock(self, mock_post):
        """Approving an article triggers both an email to subscribed readers
        and a simulated POST request to /api/approved/."""
        mail.outbox = []

        # Create unapproved article
        draft = Article.objects.create(
            title="Breaking Discovery",
            content="Sensational breaking report content.",
            author=self.journalist,
            approved=False,
        )
        self.assertEqual(len(mail.outbox), 0)
        mock_post.assert_not_called()

        # Approve the article (triggers post_save signal)
        draft.approved = True
        draft.save()

        # 1. Verify email dispatch to subscribed reader
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.reader.email, mail.outbox[0].to)
        self.assertIn("Breaking Discovery", mail.outbox[0].subject)

        # 2. Verify webhook POST call to /api/approved/
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://127.0.0.1:8000/api/approved/")
        self.assertEqual(kwargs["json"]["title"], "Breaking Discovery")
        self.assertEqual(kwargs["json"]["author"], self.journalist.username)

    # ========================================================
    # 6. NEWSLETTER RELATIONSHIPS
    # ========================================================
    def test_newsletter_creation_and_article_association(self):
        """Journalists can curate multiple articles into a newsletter."""
        newsletter = Newsletter.objects.create(
            title="Weekly Tech Recap",
            description="Handpicked highlights.",
            author=self.journalist,
        )
        newsletter.articles.add(self.article_sub1, self.article_sub2)

        self.assertEqual(newsletter.articles.count(), 2)
        self.assertEqual(newsletter.author.username, self.journalist.username)
