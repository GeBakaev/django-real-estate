import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .models import WebsiteInfo

logger = logging.getLogger(__name__)


def notify_new_contact(contact):
    """Email the site owner about a saved Contact.

    Recipients come from CONTACT_NOTIFY_EMAILS; when that is empty, notifications are
    simply off. Never raises: the submission is already stored, so a mail outage only
    logs an error.
    """
    recipients = settings.CONTACT_NOTIFY_EMAILS
    if not recipients:
        return False

    site_info = WebsiteInfo.objects.first() or WebsiteInfo()
    context = {"contact": contact, "site_info": site_info}
    message = EmailMessage(
        subject=f"[{site_info.website_name}] New inquiry: {contact.subject}",
        body=render_to_string("emails/contact_notification.txt", context),
        to=recipients,
        reply_to=[contact.email],
    )
    try:
        message.send()
    except Exception:
        logger.exception("Could not send notification for contact %s", contact.pk)
        return False
    return True
