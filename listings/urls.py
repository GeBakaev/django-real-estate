from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("properties/", views.PostList.as_view(), name="properties"),
    path("about-us/", views.about_us, name="about-us"),
    path("contact-us/", views.contact_us, name="contact-us"),
    path("<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),  # keep last
]
