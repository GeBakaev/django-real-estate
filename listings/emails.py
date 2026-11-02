import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .models import WebsiteInfo

logger = logging.getLogger(__name__)


def contact_recipients():
    """Addresses that receive new inquiries: env override, else the site's contact email."""
    if settings.CONTACT_NOTIFY_EMAILS:
        return list(settings.CONTACT_NOTIFY_EMAILS)
    site_info = WebsiteInfo.objects.first()
    return [site_info.email] if site_info and site_info.email else []


def notify_new_contact(contact):
    """Email the site owner about a saved Contact. Never raises: the visitor's
    submission is already stored, so a mail outage only logs an error."""
    recipients = contact_recipients()
    if not recipients:
        logger.warning("Contact %s saved but no notification recipient is configured", contact.pk)
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
