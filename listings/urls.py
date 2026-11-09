from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import sitemaps

urlpatterns = [
    path("", views.home, name="home"),
    path("properties/", views.PostList.as_view(), name="properties"),
    path("properties/map/", views.properties_map, name="properties-map"),
    path("about-us/", views.about_us, name="about-us"),
    path("contact-us/", views.contact_us, name="contact-us"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),  # keep last
]
