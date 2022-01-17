# Django Libs
from django.contrib import admin

# Register your models here.
from .models import Listing, Image, Contact, WebsiteInfo

# Listing Images
class ImageDetailsInline(admin.TabularInline):
    model = Image
    fields = ('name', 'listing', 'image', 'default')

# Listing
class ListingAdmin(admin.ModelAdmin):
    inlines = (ImageDetailsInline, )
    list_display = ('title', 'slug', 'price', 'location', 'created_on')
    list_filter = ("status",)
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}

# Contact
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'message', 'created_time')
    search_fields = ['email', 'subject']

# Website Info
class WebsiteInfoAdmin(admin.ModelAdmin):
    list_display = (
        'website_name', 'business_location',
        'email', 'phone_number', 'about_us',
        'facebook_link', 'instagram_link', 'linkedin_link',
        'properties_count', 'cities_count', 'offices_count'
    )

admin.site.register(Listing, ListingAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(WebsiteInfo, WebsiteInfoAdmin)