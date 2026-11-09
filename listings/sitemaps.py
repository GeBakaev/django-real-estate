from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Listing


class ListingSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Listing.objects.published()

    def lastmod(self, listing):
        return listing.updated_on


class StaticPagesSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["home", "properties", "properties-map", "about-us", "contact-us"]

    def location(self, name):
        return reverse(name)


sitemaps = {"listings": ListingSitemap, "pages": StaticPagesSitemap}
