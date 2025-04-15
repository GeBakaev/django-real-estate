from django import template
from listings.models import WebsiteInfo


register = template.Library()


def get_website_info_helper():
    # Website Info
    website_info = WebsiteInfo.objects.first()
    return website_info


@register.simple_tag
def get_website_info(property: str):
    # Website Info
    website_info = get_website_info_helper()
    return website_info.__dict__.get(property)
