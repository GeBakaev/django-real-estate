from django.contrib import admin

from .models import Contact, Image, Listing, WebsiteInfo

LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"


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
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "price", "area", "description")}),
        (
            "Location",
            {
                "fields": ("location", ("latitude", "longitude")),
                "description": "Click the map or drag the marker to set the coordinates.",
            },
        ),
    )

    class Media:
        css = {"all": (LEAFLET_CSS,)}
        js = (LEAFLET_JS, "listings/admin_map.js")


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
