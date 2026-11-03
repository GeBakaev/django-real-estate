from django.templatetags.static import static

from .models import WebsiteInfo


def seo(request):
    """Absolute URLs for canonical/Open Graph tags; the current path without its query."""
    return {
        "canonical_url": request.build_absolute_uri(request.path),
        "default_og_image": request.build_absolute_uri(static("images/hero.webp")),
    }


def website_info(request):
    """Expose the single WebsiteInfo row to every template as `site_info`.

    Falls back to an unsaved instance (model defaults) if the row is missing,
    so templates never crash on a fresh database.
    """
    return {"site_info": WebsiteInfo.objects.first() or WebsiteInfo()}
