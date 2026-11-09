import shutil
import tempfile
from io import BytesIO

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Contact, Image, Listing, WebsiteInfo

# 1x1 transparent GIF, enough for ImageField validation.
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def make_jpeg(name="photo.jpg", size=(1200, 900), color=(200, 30, 60)):
    """A real JPEG upload, since derivatives are produced with Pillow."""
    from PIL import Image as PILImage

    buffer = BytesIO()
    PILImage.new("RGB", size, color).save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def make_listing(title="Sea View Villa", status=Listing.Status.PUBLISHED, **kwargs):
    fields = {"price": 250000, "area": 180, "description": "A lovely place.", "location": "Beirut"}
    fields.update(kwargs)
    return Listing.objects.create(title=title, status=status, **fields)


class ListingModelTests(TestCase):
    def test_slug_generated_from_title(self):
        listing = make_listing(title="Sea View Villa")
        self.assertEqual(listing.slug, "sea-view-villa")

    def test_duplicate_titles_get_unique_slugs(self):
        first = make_listing(title="Same Title")
        second = make_listing(title="Same Title")
        third = make_listing(title="Same Title")
        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-2")
        self.assertEqual(third.slug, "same-title-3")

    def test_slug_is_stable_when_title_changes(self):
        listing = make_listing(title="Original")
        listing.title = "Renamed"
        listing.save()
        self.assertEqual(listing.slug, "original")

    def test_explicit_slug_is_kept(self):
        listing = make_listing(title="Whatever", slug="custom-slug")
        self.assertEqual(listing.slug, "custom-slug")

    def test_published_queryset_excludes_drafts(self):
        make_listing(title="Live")
        make_listing(title="Hidden", status=Listing.Status.DRAFT)
        self.assertEqual([item.title for item in Listing.objects.published()], ["Live"])

    def test_cover_image_prefers_default(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            self._assert_cover_image_prefers_default()

    def _assert_cover_image_prefers_default(self):
        listing = make_listing()
        Image.objects.create(
            listing=listing, name="first", image=SimpleUploadedFile("a.gif", TINY_GIF)
        )
        cover = Image.objects.create(
            listing=listing, name="cover", image=SimpleUploadedFile("b.gif", TINY_GIF), default=True
        )
        self.assertEqual(listing.cover_image, cover)


class ListingViewTests(TestCase):
    def test_home_shows_three_most_recent_published(self):
        for i in range(4):
            make_listing(title=f"Listing {i}")
        make_listing(title="Draft", status=Listing.Status.DRAFT)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        titles = [item.title for item in response.context["listing_list"]]
        self.assertEqual(len(titles), 3)
        self.assertNotIn("Draft", titles)

    def test_properties_page_paginates_published_only(self):
        for i in range(10):
            make_listing(title=f"Listing {i}")
        make_listing(title="Draft", status=Listing.Status.DRAFT)
        response = self.client.get(reverse("properties"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 9)
        self.assertEqual(response.context["paginator"].count, 10)

    def test_detail_renders_published_listing(self):
        listing = make_listing()
        response = self.client.get(listing.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sea View Villa")
        self.assertContains(response, "$250,000")

    def test_detail_404_for_draft(self):
        listing = make_listing(status=Listing.Status.DRAFT)
        response = self.client.get(listing.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_about_and_contact_render(self):
        for name in ("about-us", "contact-us"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_base_layout_uses_compiled_stylesheet(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "css/site.css")
        self.assertNotContains(response, "bootstrap")

    def test_active_nav_link_marked(self):
        response = self.client.get(reverse("about-us"))
        self.assertContains(response, 'aria-current="page"', count=2)  # desktop + mobile menus
        self.assertContains(response, 'href="/about-us/" class="nav-link nav-link-active"')

    def test_properties_pagination_links(self):
        for i in range(10):
            make_listing(title=f"Listing {i}")
        response = self.client.get(reverse("properties"))
        self.assertContains(response, 'href="?page=2#properties"')
        self.assertContains(response, 'aria-label="Next page"')
        self.assertNotContains(response, 'aria-label="Previous page"')

    def test_properties_empty_state(self):
        response = self.client.get(reverse("properties"))
        self.assertContains(response, "No properties have been published yet")


class ListingFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cheap = make_listing(
            title="Studio in Tripoli", location="Tripoli", price=90000, area=45
        )
        cls.mid = make_listing(title="Flat in Beirut", location="Beirut", price=250000, area=120)
        cls.big = make_listing(title="Villa in Batroun", location="Batroun", price=900000, area=400)
        make_listing(title="Draft in Beirut", location="Beirut", status=Listing.Status.DRAFT)

    def titles(self, **params):
        response = self.client.get(reverse("properties"), params)
        self.assertEqual(response.status_code, 200)
        return [item.title for item in response.context["page_obj"]]

    def test_default_order_is_newest_first(self):
        self.assertEqual(self.titles(), ["Villa in Batroun", "Flat in Beirut", "Studio in Tripoli"])

    def test_filter_by_location(self):
        self.assertEqual(self.titles(location="Beirut"), ["Flat in Beirut"])

    def test_filter_by_price_range(self):
        self.assertEqual(self.titles(min_price=100000, max_price=300000), ["Flat in Beirut"])

    def test_filter_by_min_area(self):
        self.assertEqual(self.titles(min_area=120), ["Villa in Batroun", "Flat in Beirut"])

    def test_search_matches_title_and_location(self):
        self.assertEqual(self.titles(q="villa"), ["Villa in Batroun"])
        self.assertEqual(self.titles(q="tripoli"), ["Studio in Tripoli"])

    def test_sort_by_price(self):
        self.assertEqual(
            self.titles(sort="price_asc"),
            ["Studio in Tripoli", "Flat in Beirut", "Villa in Batroun"],
        )
        self.assertEqual(self.titles(sort="price_desc")[0], "Villa in Batroun")

    def test_invalid_values_are_ignored(self):
        self.assertEqual(len(self.titles(min_price="abc", sort="bogus", min_bedrooms="9")), 3)

    def test_filter_by_property_type_and_bedrooms(self):
        Listing.objects.filter(pk=self.big.pk).update(property_type="villa", bedrooms=4)
        Listing.objects.filter(pk=self.mid.pk).update(property_type="apartment", bedrooms=2)
        self.assertEqual(self.titles(property_type="villa"), ["Villa in Batroun"])
        self.assertEqual(self.titles(min_bedrooms=2), ["Villa in Batroun", "Flat in Beirut"])
        self.assertEqual(self.titles(min_bedrooms=3), ["Villa in Batroun"])
        self.assertEqual(len(self.titles(property_type="castle")), 3)

    def test_location_choices_only_from_published(self):
        response = self.client.get(reverse("properties"))
        choices = [value for value, _ in response.context["filter_form"].fields["location"].choices]
        self.assertEqual(choices, ["", "Batroun", "Beirut", "Tripoli"])

    def test_results_count_mentions_filters(self):
        response = self.client.get(reverse("properties"), {"location": "Beirut"})
        self.assertContains(response, "1 property matches your filters")
        response = self.client.get(reverse("properties"), {"min_price": 5_000_000})
        self.assertContains(response, "No properties match these filters")

    def test_htmx_request_gets_results_partial(self):
        response = self.client.get(
            reverse("properties"), {"location": "Beirut"}, headers={"HX-Request": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flat in Beirut")
        self.assertNotContains(response, "<html")
        self.assertIn("HX-Request", response.headers["Vary"])

    def test_pagination_keeps_filters(self):
        for i in range(9):
            make_listing(title=f"Beirut {i}", location="Beirut")
        response = self.client.get(
            reverse("properties"), {"location": "Beirut", "sort": "price_asc"}
        )
        self.assertContains(
            response, 'href="?location=Beirut&amp;sort=price_asc&amp;page=2#properties"'
        )


class SaleOrRentTests(TestCase):
    def make_rental(self, **kwargs):
        fields = {
            "title": "Furnished Flat in Hamra",
            "location": "Beirut",
            "price": 1500,
            "listing_type": Listing.ListingType.RENT,
            "rent_period": Listing.RentPeriod.MONTH,
        }
        fields.update(kwargs)
        return make_listing(**fields)

    def test_defaults_to_sale_with_plain_price_label(self):
        listing = make_listing(price=850000)
        self.assertEqual(listing.listing_type, "sale")
        self.assertFalse(listing.is_rental)
        self.assertEqual(listing.price_label, "$850,000")

    def test_rental_price_label_includes_period(self):
        self.assertEqual(self.make_rental().price_label, "$1,500 / month")
        yearly = self.make_rental(title="Yearly", price=14000, rent_period="year")
        self.assertEqual(yearly.price_label, "$14,000 / year")

    def test_rental_requires_a_period(self):
        listing = Listing(
            title="No period", price=900, listing_type="rent", location="Beirut", description="x"
        )
        with self.assertRaises(ValidationError) as caught:
            listing.full_clean()
        self.assertIn("rent_period", caught.exception.message_dict)

    def test_sale_drops_a_leftover_period(self):
        listing = self.make_rental()
        listing.listing_type = Listing.ListingType.SALE
        listing.save()
        listing.refresh_from_db()
        self.assertEqual(listing.rent_period, "")
        self.assertEqual(listing.price_label, "$1,500")

    def test_filter_by_listing_type(self):
        make_listing(title="Villa for sale", price=900000)
        self.make_rental()

        def titles(**params):
            response = self.client.get(reverse("properties"), params)
            return [item.title for item in response.context["page_obj"]]

        self.assertEqual(titles(listing_type="rent"), ["Furnished Flat in Hamra"])
        self.assertEqual(titles(listing_type="sale"), ["Villa for sale"])
        self.assertEqual(len(titles()), 2)
        self.assertEqual(len(titles(listing_type="lease")), 2)

    def test_cards_and_detail_show_type_and_period(self):
        rental = self.make_rental()
        response = self.client.get(reverse("properties"))
        self.assertContains(response, "For rent")
        self.assertContains(response, "$1,500 / month")
        response = self.client.get(rental.get_absolute_url())
        self.assertContains(response, "For rent")
        self.assertContains(response, "$1,500 / month")
        self.assertContains(
            response, 'property="og:title" content="Furnished Flat in Hamra · $1,500 / month"'
        )


class MapViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.beirut = make_listing(
            title="Flat in Beirut", location="Beirut", latitude="33.8886", longitude="35.5205"
        )
        cls.batroun = make_listing(
            title="Villa in Batroun",
            location="Batroun",
            price=850000,
            latitude="34.2553",
            longitude="35.6581",
        )
        make_listing(title="No coordinates", location="Beirut")
        make_listing(
            title="Draft pin",
            status=Listing.Status.DRAFT,
            latitude="33.9",
            longitude="35.5",
        )

    def test_map_page_lists_located_published_listings(self):
        response = self.client.get(reverse("properties-map"))
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.context["markers"]]
        self.assertEqual(sorted(titles), ["Flat in Beirut", "Villa in Batroun"])
        self.assertContains(response, 'id="listing-map-data"')
        self.assertContains(response, "2 properties on the map, 1 more without a location")
        self.assertContains(response, "leaflet@1.9.4")
        villa = next(item for item in response.context["markers"] if "Villa" in item["title"])
        self.assertEqual(villa["price"], "$850,000")
        self.assertEqual(villa["url"], self.batroun.get_absolute_url())
        self.assertAlmostEqual(villa["lat"], 34.2553)

    def test_map_respects_filters(self):
        response = self.client.get(reverse("properties-map"), {"location": "Batroun"})
        titles = [item["title"] for item in response.context["markers"]]
        self.assertEqual(titles, ["Villa in Batroun"])
        self.assertContains(response, "1 property on the map")
        self.assertNotContains(response, "without a location")

    def test_map_empty_state(self):
        response = self.client.get(reverse("properties-map"), {"min_price": 5_000_000})
        self.assertContains(response, "No properties with a location match these filters.")
        self.assertNotContains(response, 'id="listing-map-data"')
        self.assertNotContains(response, "leaflet@1.9.4")

    def test_toggle_links_keep_filters_and_drop_page(self):
        response = self.client.get(reverse("properties"), {"location": "Beirut", "page": 1})
        self.assertContains(response, 'href="/properties/map/?location=Beirut#properties"')
        response = self.client.get(reverse("properties-map"), {"location": "Beirut"})
        self.assertContains(response, 'href="/properties/?location=Beirut#properties"')
        response = self.client.get(reverse("properties"))
        self.assertContains(response, 'href="/properties/map/#properties"')

    def test_map_page_in_sitemap(self):
        response = self.client.get(reverse("sitemap"))
        self.assertContains(response, "http://testserver/properties/map/")


class SiteCopyAndPolishTests(TestCase):
    def test_hero_copy_comes_from_website_info(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(
            hero_tagline="Coast and mountains",
            hero_title="Homes worth coming back to",
            hero_subtitle="Sold by people who know every street.",
            about_headline="Thirty years on the coast",
        )
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Coast and mountains")
        self.assertContains(response, "Homes worth coming back to")
        self.assertContains(response, "Sold by people who know every street.")
        self.assertContains(self.client.get(reverse("about-us")), "Thirty years on the coast")

    def test_empty_tagline_hides_the_pill(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(hero_tagline="", hero_subtitle="")
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "eyebrow-pill")
        self.assertContains(response, "Premier real estate")

    def test_favicon_linked(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'rel="icon" href="/static/images/favicon.svg"')

    def test_404_uses_site_layout(self):
        response = self.client.get("/no-such-listing/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "Browse properties", status_code=404)
        self.assertContains(response, "css/site.css", status_code=404)

    def test_500_template_renders_without_context(self):
        from django.template.loader import render_to_string

        html = render_to_string("500.html")
        self.assertIn("Something went wrong", html)
        self.assertIn("css/site.css", html)

    def test_admin_is_branded_with_site_name(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(website_name="Acme Homes")
        response = self.client.get("/admin/login/")
        self.assertContains(response, "Acme Homes admin")
        self.assertNotContains(response, "Django administration")

    def test_oversized_photo_is_rejected(self):
        from unittest import mock

        from django.core.exceptions import ValidationError

        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            listing = make_listing()
            photo = Image(listing=listing, name="Front", image=make_jpeg())
            photo.full_clean()  # within the limit
            with mock.patch("listings.images.MAX_UPLOAD_BYTES", 100):
                with self.assertRaises(ValidationError) as caught:
                    photo.full_clean()
            self.assertIn("too large", str(caught.exception))


class SeoTests(TestCase):
    def test_sitemap_lists_published_listings_and_pages(self):
        listing = make_listing(title="Listed")
        make_listing(title="Hidden", status=Listing.Status.DRAFT)
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(f"http://testserver{listing.get_absolute_url()}", body)
        self.assertNotIn("hidden", body)
        self.assertIn("<lastmod>", body)
        for name in ("properties", "about-us", "contact-us"):
            self.assertIn(f"http://testserver{reverse(name)}", body)

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_canonical_drops_query_string(self):
        response = self.client.get(reverse("properties"), {"location": "Beirut", "page": 1})
        self.assertContains(response, '<link rel="canonical" href="http://testserver/properties/">')

    def test_home_uses_default_open_graph_image(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, '<meta property="og:type" content="website">')
        self.assertContains(
            response,
            '<meta property="og:image" content="http://testserver/static/images/hero.webp">',
        )

    def test_listing_open_graph_uses_cover_photo(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            listing = make_listing(
                title="Sea View Villa",
                price=250000,
                description="A lovely place.\n\nWith <b>two</b> paragraphs.",
            )
            cover = Image.objects.create(listing=listing, name="Front", image=make_jpeg())
            response = self.client.get(listing.get_absolute_url())
            self.assertContains(
                response, '<meta property="og:title" content="Sea View Villa · $250,000">'
            )
            self.assertContains(
                response, f'<meta property="og:image" content="http://testserver{cover.large.url}">'
            )
            self.assertContains(
                response,
                'property="og:description" content="Beirut. A lovely place. With two paragraphs."',
            )
            self.assertContains(
                response, '<meta name="description" content="A lovely place. With two paragraphs.">'
            )


class ListingAttributeTests(TestCase):
    def test_specs_rendered_on_card_and_detail(self):
        make_listing(title="Family House", property_type="house", bedrooms=3, bathrooms=1, area=200)
        response = self.client.get(reverse("properties"))
        self.assertContains(response, "House")
        self.assertContains(response, "3 beds")
        self.assertContains(response, "1 bath<")
        self.assertContains(response, "200 m²")
        response = self.client.get(Listing.objects.get(title="Family House").get_absolute_url())
        self.assertContains(response, "3 beds")

    def test_land_without_rooms_shows_only_area(self):
        land = make_listing(title="Plot", property_type="land", area=900)
        response = self.client.get(land.get_absolute_url())
        self.assertContains(response, "Land")
        self.assertContains(response, "900 m²")
        self.assertNotContains(response, "bed")
        self.assertNotContains(response, "bath")

    def test_defaults_are_empty(self):
        listing = make_listing()
        self.assertEqual(listing.property_type, "")
        self.assertIsNone(listing.bedrooms)
        self.assertNotContains(self.client.get(listing.get_absolute_url()), "bed")


class ThumbnailTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.listing = make_listing()

    def dimensions(self, field):
        from PIL import Image as PILImage

        with field.open("rb") as handle, PILImage.open(handle) as im:
            return im.size, im.format

    def test_derivatives_generated_on_create(self):
        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        self.assertEqual(self.dimensions(image.card), ((800, 600), "WEBP"))
        self.assertEqual(self.dimensions(image.thumb), ((320, 240), "WEBP"))
        self.assertEqual(self.dimensions(image.large), ((1200, 900), "WEBP"))  # never upscaled
        self.assertTrue(image.card.name.startswith("images/card/photo-card"))
        self.assertEqual(Image.objects.get(pk=image.pk).card.name, image.card.name)

    def test_large_shrinks_big_uploads(self):
        image = Image.objects.create(
            listing=self.listing, name="Huge", image=make_jpeg(size=(4000, 2000))
        )
        self.assertEqual(self.dimensions(image.large)[0], (1600, 800))

    def test_replacing_upload_regenerates_and_removes_old_files(self):
        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        old_card = image.card.name
        image.image = make_jpeg(name="other.jpg", size=(1000, 1000))
        image.save()
        self.assertNotEqual(image.card.name, old_card)
        self.assertTrue(image.card.name.startswith("images/card/other-card"))
        self.assertFalse(image.card.storage.exists(old_card))
        self.assertEqual(self.dimensions(image.large)[0], (1000, 1000))

    def test_unrelated_save_does_not_regenerate(self):
        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        from unittest import mock

        with mock.patch.object(Image, "generate_derivatives") as generate:
            image.default = True
            image.save()
        generate.assert_not_called()

    def test_delete_removes_all_files(self):
        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        names = [image.image.name, image.large.name, image.card.name, image.thumb.name]
        storage = image.image.storage
        self.assertTrue(all(storage.exists(name) for name in names))
        image.delete()
        self.assertFalse(any(storage.exists(name) for name in names))

    def test_urls_fall_back_to_original(self):
        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        Image.objects.filter(pk=image.pk).update(large="", card="", thumb="")
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(image.card_url, image.image.url)
        response = self.client.get(self.listing.get_absolute_url())
        self.assertContains(response, image.image.url)

    def test_make_thumbnails_backfills_missing(self):
        from io import StringIO

        from django.core.management import call_command

        image = Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        Image.objects.filter(pk=image.pk).update(large="", card="", thumb="")
        out = StringIO()
        call_command("make_thumbnails", stdout=out)
        self.assertIn("1 image(s), 0 failed", out.getvalue())
        self.assertTrue(Image.objects.get(pk=image.pk).has_derivatives)
        out = StringIO()
        call_command("make_thumbnails", stdout=out)
        self.assertIn("0 image(s)", out.getvalue())

    def test_card_and_gallery_use_derivatives(self):
        Image.objects.create(listing=self.listing, name="Front", image=make_jpeg())
        Image.objects.create(listing=self.listing, name="Back", image=make_jpeg(name="back.jpg"))
        response = self.client.get(reverse("properties"))
        self.assertContains(response, "/media/images/card/photo-card")
        response = self.client.get(self.listing.get_absolute_url())
        self.assertContains(response, "/media/images/large/photo-large")
        self.assertContains(response, "/media/images/thumb/back-thumb")


class GalleryTests(TestCase):
    def setUp(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        self.override = override_settings(MEDIA_ROOT=media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.listing = make_listing()

    def add_image(self, name, default=False):
        return Image.objects.create(
            listing=self.listing,
            name=name,
            image=SimpleUploadedFile(f"{name}.gif", TINY_GIF),
            default=default,
        )

    def test_gallery_images_put_cover_first(self):
        first = self.add_image("first")
        cover = self.add_image("cover", default=True)
        self.assertEqual(self.listing.gallery_images, [cover, first])
        self.assertEqual(Listing.objects.get(pk=self.listing.pk).gallery_images, [cover, first])

    def test_single_image_has_no_controls(self):
        self.add_image("only")
        response = self.client.get(self.listing.get_absolute_url())
        self.assertContains(response, "data-gallery-main")
        self.assertNotContains(response, "data-gallery-thumb")
        self.assertNotContains(response, "data-gallery-next")

    def test_multiple_images_render_thumbnails_and_script(self):
        self.add_image("a")
        self.add_image("b")
        self.add_image("c")
        response = self.client.get(self.listing.get_absolute_url())
        self.assertContains(response, "data-gallery-thumb", count=3)
        self.assertContains(response, "1 / 3")
        self.assertContains(response, "js/gallery.js")

    def test_no_images_no_gallery(self):
        response = self.client.get(self.listing.get_absolute_url())
        self.assertNotContains(response, "data-gallery")
        self.assertNotContains(response, "js/gallery.js")


class ContactFormTests(TestCase):
    payload = {
        "name": "Jane",
        "email": "jane@example.com",
        "subject": "Viewing",
        "message": "Can I see the villa?",
    }

    def test_valid_post_saves_and_redirects(self):
        response = self.client.post(reverse("contact-us"), self.payload, follow=True)
        self.assertRedirects(response, reverse("contact-us"))
        self.assertEqual(Contact.objects.count(), 1)
        self.assertContains(response, "Thank you for contacting us")

    def test_home_form_also_works(self):
        response = self.client.post(reverse("home"), self.payload)
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Contact.objects.count(), 1)

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test", "sales@acme.test"])
    def test_valid_post_notifies_configured_recipients(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(website_name="Acme Homes")
        self.client.post(reverse("contact-us"), self.payload)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["owner@acme.test", "sales@acme.test"])
        self.assertEqual(sent.reply_to, ["jane@example.com"])
        self.assertEqual(sent.subject, "[Acme Homes] New inquiry: Viewing")
        self.assertIn("Can I see the villa?", sent.body)
        self.assertIn("Jane <jane@example.com>", sent.body)

    @override_settings(CONTACT_NOTIFY_EMAILS=[])
    def test_no_recipients_means_no_email(self):
        response = self.client.post(reverse("contact-us"), self.payload)
        self.assertRedirects(response, reverse("contact-us"))
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test"])
    def test_mail_failure_does_not_break_submission(self):
        from unittest import mock

        with (
            mock.patch("listings.emails.EmailMessage.send", side_effect=OSError("smtp down")),
            self.assertLogs("listings.emails", level="ERROR") as logs,
        ):
            response = self.client.post(reverse("contact-us"), self.payload)
        self.assertRedirects(response, reverse("contact-us"))
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIn("Could not send notification", logs.output[0])

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test"])
    def test_invalid_post_sends_nothing(self):
        self.client.post(reverse("contact-us"), {**self.payload, "email": "nope"})
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_post_rerenders_with_errors(self):
        response = self.client.post(
            reverse("contact-us"), {**self.payload, "email": "not-an-email"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertTrue(response.context["form"].errors)
        self.assertContains(response, "Enter a valid email address.")


class ListingInquiryTests(TestCase):
    payload = {
        "name": "Jane",
        "email": "jane@example.com",
        "subject": "Inquiry about Sea View Villa",
        "message": "Can I see it on Saturday?",
    }

    def setUp(self):
        self.listing = make_listing(title="Sea View Villa")
        self.url = self.listing.get_absolute_url()

    def test_listing_page_has_form_with_prefilled_subject(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'id="inquiry"')
        self.assertContains(
            response,
            '<input type="hidden" name="subject" value="Inquiry about Sea View Villa"',
        )
        self.assertContains(response, "Send inquiry")

    def test_valid_post_links_inquiry_to_listing(self):
        response = self.client.post(self.url, self.payload, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Thank you for contacting us")
        contact = Contact.objects.get()
        self.assertEqual(contact.listing, self.listing)
        self.assertEqual(contact.subject, "Inquiry about Sea View Villa")
        self.assertEqual(list(self.listing.inquiries.all()), [contact])

    def test_invalid_post_rerenders_listing_with_errors(self):
        response = self.client.post(self.url, {**self.payload, "email": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address.")
        # What the visitor typed is kept.
        self.assertContains(response, "Can I see it on Saturday?")

    def test_draft_listing_cannot_receive_inquiries(self):
        draft = make_listing(title="Hidden", status=Listing.Status.DRAFT)
        response = self.client.post(draft.get_absolute_url(), self.payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Contact.objects.count(), 0)

    def test_contact_page_inquiry_has_no_listing(self):
        self.client.post(reverse("contact-us"), self.payload)
        self.assertIsNone(Contact.objects.get().listing)

    def test_inquiry_survives_listing_deletion(self):
        self.client.post(self.url, self.payload)
        self.listing.delete()
        self.assertIsNone(Contact.objects.get().listing)

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test"])
    def test_notification_names_the_listing(self):
        self.client.post(self.url, self.payload)
        body = mail.outbox[0].body
        self.assertIn("Listing: Sea View Villa", body)
        self.assertIn(f"http://testserver{self.url}", body)

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test"])
    def test_general_notification_has_no_listing_line(self):
        self.client.post(reverse("contact-us"), self.payload)
        self.assertNotIn("Listing:", mail.outbox[0].body)

    @override_settings(CONTACT_NOTIFY_EMAILS=["owner@acme.test"])
    def test_notification_is_plain_text_not_html_escaped(self):
        payload = {**self.payload, "name": "O'Brien & Sons", "message": "Is it < 500k?"}
        self.client.post(self.url, payload)
        body = mail.outbox[0].body
        self.assertIn("O'Brien & Sons <jane@example.com>", body)
        self.assertIn("Is it < 500k?", body)

    def test_whatsapp_hidden_without_a_number(self):
        self.assertNotContains(self.client.get(self.url), "wa.me")
        self.assertNotContains(self.client.get(reverse("contact-us")), "wa.me")

    def test_whatsapp_button_links_to_number_with_listing_message(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(whatsapp_number="+961 70 123 456")
        response = self.client.get(self.url)
        self.assertContains(response, "https://wa.me/96170123456?text=Hello%2C%20I%20am")
        self.assertContains(response, "Sea%20View%20Villa")
        self.assertContains(response, "http%3A%2F%2Ftestserver%2F")
        self.assertContains(self.client.get(reverse("contact-us")), "https://wa.me/96170123456")

    def test_admin_lists_the_listing_of_an_inquiry(self):
        from django.contrib.auth import get_user_model

        self.client.post(self.url, self.payload)
        admin_user = get_user_model().objects.create_superuser("boss", "boss@acme.test", "pw")
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:listings_contact_changelist"))
        self.assertContains(response, "Sea View Villa")


class WebsiteInfoTests(TestCase):
    def test_site_info_in_context_from_db(self):
        WebsiteInfo.objects.all().delete()
        WebsiteInfo.objects.create(website_name="Acme Homes")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Acme Homes")

    def test_site_info_falls_back_to_defaults_when_missing(self):
        WebsiteInfo.objects.all().delete()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["site_info"].website_name, "Real Estate Website")


class EnsureSuperuserCommandTests(TestCase):
    def _run(self, **env):
        from io import StringIO
        from unittest import mock

        from django.core.management import call_command

        out = StringIO()
        with mock.patch.dict("os.environ", env, clear=False):
            call_command("ensure_superuser", stdout=out)
        return out.getvalue()

    def test_creates_admin_from_env(self):
        from django.contrib.auth import get_user_model

        self._run(
            DJANGO_ADMIN_USERNAME="boss",
            DJANGO_ADMIN_EMAIL="boss@example.com",
            DJANGO_ADMIN_PASSWORD="s3cret-pass",
        )
        user = get_user_model().objects.get(username="boss")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("s3cret-pass"))

    def test_skips_when_password_missing(self):
        from django.contrib.auth import get_user_model

        output = self._run(DJANGO_ADMIN_USERNAME="boss", DJANGO_ADMIN_PASSWORD="")
        self.assertIn("skipping", output)
        self.assertFalse(get_user_model().objects.filter(username="boss").exists())

    def test_idempotent(self):
        from django.contrib.auth import get_user_model

        env = {"DJANGO_ADMIN_USERNAME": "boss", "DJANGO_ADMIN_PASSWORD": "s3cret-pass"}
        self._run(**env)
        output = self._run(**env)
        self.assertIn("already exists", output)
        self.assertEqual(get_user_model().objects.filter(username="boss").count(), 1)


class CoordinateTests(TestCase):
    def test_has_coordinates(self):
        self.assertFalse(make_listing().has_coordinates)
        listing = make_listing(title="Located", latitude="33.893800", longitude="35.501800")
        self.assertTrue(listing.has_coordinates)

    def test_out_of_range_coordinates_fail_validation(self):
        from django.core.exceptions import ValidationError

        listing = make_listing(title="Bad", latitude=95, longitude=0)
        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_detail_renders_map_only_with_coordinates(self):
        without = make_listing(title="No map")
        response = self.client.get(without.get_absolute_url())
        self.assertNotContains(response, 'id="map"')

        with_map = make_listing(title="With map", latitude="33.893800", longitude="35.501800")
        response = self.client.get(with_map.get_absolute_url())
        self.assertContains(response, 'id="map"')
        self.assertContains(response, 'data-lat="33.893800"')
        self.assertContains(response, "leaflet.js")

    def test_position_parser_from_migration(self):
        from decimal import Decimal
        from importlib import import_module

        parse = import_module("listings.migrations.0004_listing_latitude_longitude").parse_position
        self.assertEqual(parse("33.8938,35.5018"), (Decimal("33.8938"), Decimal("35.5018")))
        self.assertEqual(parse("33.8938, 35.5018"), (Decimal("33.8938"), Decimal("35.5018")))
        self.assertEqual(parse("0, 0"), (None, None))
        self.assertEqual(parse(""), (None, None))
        self.assertEqual(parse(None), (None, None))
        self.assertEqual(parse("garbage"), (None, None))
        self.assertEqual(parse("95,10"), (None, None))
