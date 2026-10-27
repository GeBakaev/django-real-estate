from .models import WebsiteInfo


def website_info(request):
    """Expose the single WebsiteInfo row to every template as `site_info`.

    Falls back to an unsaved instance (model defaults) if the row is missing,
    so templates never crash on a fresh database.
    """
    return {"site_info": WebsiteInfo.objects.first() or WebsiteInfo()}
