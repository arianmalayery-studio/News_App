import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Article, CustomUser


@receiver(post_save, sender=Article)
def handle_article_approval(sender, instance, created, **kwargs):
    """Triggers subscriber notifications and internal API logging."""
    if not instance.approved:
        return

    # 1. Identify all subscribed readers
    recipient_emails = set()

    # Readers subscribed to the journalist author
    journalist_subscribers = CustomUser.objects.filter(
        role=CustomUser.Role.READER, subscribed_journalists=instance.author
    ).values_list("email", flat=True)
    recipient_emails.update([e for e in journalist_subscribers if e])

    # Readers subscribed to the publisher[cite: 4]
    if instance.publisher:
        publisher_subscribers = CustomUser.objects.filter(
            role=CustomUser.Role.READER,
            subscribed_publishers=instance.publisher,
        ).values_list("email", flat=True)
        recipient_emails.update([e for e in publisher_subscribers if e])

    # 2. Send email notification
    if recipient_emails:
        author_name = (
            instance.author.get_full_name() or instance.author.username
        )
        pub_name = (
            instance.publisher.name if instance.publisher else "Independent"
        )
        subject = f"New Published Article: {instance.title}"
        message = (
            f"An article you are subscribed to has been published!\n\n"
            f"Title: {instance.title}\n"
            f"Author: {author_name}\n"
            f"Publisher: {pub_name}\n\n"
            f"{instance.content[:300]}..."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "news@example.com"
            ),
            recipient_list=list(recipient_emails),
            fail_silently=True,
        )

    # 3. Trigger POST to internal API logging endpoint
    payload = {
        "article_id": instance.id,
        "title": instance.title,
        "author": instance.author.username,
        "publisher": instance.publisher.name if instance.publisher else None,
        "approved_at": instance.updated_at.isoformat(),
    }

    try:
        requests.post(
            "http://127.0.0.1:8000/api/approved/", json=payload, timeout=3
        )
    except requests.RequestException:
        pass
