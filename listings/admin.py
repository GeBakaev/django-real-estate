from django.contrib import admin

from .models import Contact, Image, Listing, WebsiteInfo


class ImageInline(admin.TabularInline):
    model = Image
    fields = ("name", "image", "default")
    extra = 1


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = (ImageInline,)
    list_display = ("title", "status", "price", "location", "created_on")
    list_filter = ("status",)
    search_fields = ("title", "description", "location")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_time")
    search_fields = ("name", "email", "subject")
    readonly_fields = ("name", "email", "subject", "message", "created_time")

    def has_add_permission(self, request):
        return False


@admin.register(WebsiteInfo)
class WebsiteInfoAdmin(admin.ModelAdmin):
    list_display = ("website_name", "business_location", "email", "phone_number")

    def has_add_permission(self, request):
        return WebsiteInfo.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False
