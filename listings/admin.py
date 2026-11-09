from django.contrib import admin
from django.utils.html import format_html

from .models import Contact, Image, Listing, WebsiteInfo

LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"


class ImageInline(admin.TabularInline):
    model = Image
    fields = ("preview", "name", "image", "default")
    readonly_fields = ("preview",)
    extra = 1

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.pk or not obj.image:
            return ""
        return format_html(
            '<img src="{}" alt="" style="height: 60px; border-radius: 4px;">', obj.thumb_url
        )


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = (ImageInline,)
    list_display = (
        "title",
        "status",
        "listing_type",
        "property_type",
        "price_label",
        "bedrooms",
        "location",
        "created_on",
    )
    list_filter = ("status", "listing_type", "property_type")
    search_fields = ("title", "description", "location")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "status",
                    ("listing_type", "rent_period"),
                    "property_type",
                    ("price", "area"),
                    ("bedrooms", "bathrooms"),
                    "description",
                )
            },
        ),
        (
            "Location",
            {
                "fields": ("location", ("latitude", "longitude")),
                "description": "Click the map or drag the marker to set the coordinates.",
            },
        ),
    )

    @admin.display(description="Price", ordering="price")
    def price_label(self, obj):
        return obj.price_label

    class Media:
        css = {"all": (LEAFLET_CSS,)}
        js = (LEAFLET_JS, "listings/admin_map.js")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "listing", "created_time")
    list_select_related = ("listing",)
    search_fields = ("name", "email", "subject", "listing__title")
    readonly_fields = ("name", "email", "subject", "message", "listing", "created_time")

    def has_add_permission(self, request):
        return False


@admin.register(WebsiteInfo)
class WebsiteInfoAdmin(admin.ModelAdmin):
    list_display = ("website_name", "business_location", "email", "phone_number")
    fieldsets = (
        (None, {"fields": ("website_name", "business_location")}),
        (
            "Contact and social",
            {
                "fields": (
                    ("email", "phone_number"),
                    "whatsapp_number",
                    "facebook_link",
                    "instagram_link",
                    "linkedin_link",
                )
            },
        ),
        ("Home page", {"fields": ("hero_title", "hero_subtitle")}),
        (
            "About page",
            {
                "fields": (
                    "about_headline",
                    "about_us",
                    ("properties_count", "cities_count", "offices_count"),
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return WebsiteInfo.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False
