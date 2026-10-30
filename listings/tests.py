import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Contact, Image, Listing, WebsiteInfo

# 1x1 transparent GIF, enough for ImageField validation.
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def make_listing(title="Sea View Villa", status=Listing.Status.PUBLISHED, **kwargs):
    return Listing.objects.create(
        title=title,
        price=250000,
        area=180,
        description="A lovely place.",
        location="Beirut",
        status=status,
        **kwargs,
    )


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
        self.assertEqual([l.title for l in Listing.objects.published()], ["Live"])

    def test_cover_image_prefers_default(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media_root):
            self._assert_cover_image_prefers_default()

    def _assert_cover_image_prefers_default(self):
        listing = make_listing()
        Image.objects.create(listing=listing, name="first", image=SimpleUploadedFile("a.gif", TINY_GIF))
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
        titles = [l.title for l in response.context["listing_list"]]
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

    def test_invalid_post_rerenders_with_errors(self):
        response = self.client.post(reverse("contact-us"), {**self.payload, "email": "not-an-email"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertTrue(response.context["form"].errors)


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
