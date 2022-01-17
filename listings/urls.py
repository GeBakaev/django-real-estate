# Django Libs
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Views
from . import views

urlpatterns = [
    path('', views.HomePage, name='home'),
    path('properties/', views.PostList.as_view(), name='properties'),
    path('about-us/', views.about_us, name='about-us'),
    path('contact-us/', views.contact_us, name='contact-us'),
    path('<slug:slug>/', views.PostDetail.as_view(), name='post_detail'), # Keep Last
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)