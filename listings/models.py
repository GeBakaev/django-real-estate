from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify

from .images import SIZES, derivative_name, make_derivative, validate_upload_size


class ListingQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Listing.Status.PUBLISHED)


class Listing(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, "Draft"
        PUBLISHED = 1, "Published"

    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        HOUSE = "house", "House"
        VILLA = "villa", "Villa"
        LAND = "land", "Land"
        COMMERCIAL = "commercial", "Commercial"

    class ListingType(models.TextChoices):
        SALE = "sale", "For sale"
        RENT = "rent", "For rent"

    class RentPeriod(models.TextChoices):
        MONTH = "month", "Per month"
        YEAR = "year", "Per year"

    listing_id = models.AutoField(db_column="id", primary_key=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="URL identifier. Generated from the title when left blank.",
    )
    listing_type = models.CharField(
        max_length=4, choices=ListingType.choices, default=ListingType.SALE
    )
    price = models.IntegerField(default=0, help_text="Total price, or the rent per period.")
    rent_period = models.CharField(
        max_length=5,
        choices=RentPeriod.choices,
        blank=True,
        default="",
        help_text="Rentals only: the period the rent covers, which is also the minimum term.",
    )
    area = models.IntegerField(default=0, help_text="Area in square metres.")
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        blank=True,
        default="",
        help_text="Shown on the listing and used by the type filter.",
    )
    bedrooms = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Leave empty for land or commercial property."
    )
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=Status.choices, default=Status.DRAFT)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        if not self.is_rental:
            self.rent_period = ""
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    def clean(self):
        if self.is_rental and not self.rent_period:
            raise ValidationError({"rent_period": "Choose the rent period for a rental."})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_rental(self):
        return self.listing_type == self.ListingType.RENT

    @property
    def price_suffix(self):
        """ " / month" or " / year" for rentals, empty for sales."""
        if self.is_rental and self.rent_period:
            return f" / {self.rent_period}"
        return ""

    @property
    def price_label(self):
        """Price as shown everywhere on the site, e.g. "$850,000" or "$1,200 / month"."""
        return f"${intcomma(self.price)}{self.price_suffix}"

    @property
    def summary(self):
        """Single-line description excerpt for meta tags and previews."""
        return Truncator(" ".join(strip_tags(self.description).split())).chars(155)

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def gallery_images(self):
        """All images with the cover first. Uses the prefetched images when available."""
        images = list(self.images.all())
        if not images:
            return []
        cover = next((img for img in images if img.default), images[0])
        return [cover] + [img for img in images if img is not cover]

    @property
    def cover_image(self):
        """First image marked as default, else the first image, else None."""
        images = self.gallery_images
        return images[0] if images else None

    def _build_unique_slug(self):
        base = slugify(self.title) or "listing"
        slug = base
        counter = 2
        existing = Listing.objects.exclude(pk=self.pk)
        while existing.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug


class Image(models.Model):
    image_id = models.AutoField(db_column="id", primary_key=True)
    name = models.CharField(max_length=255, help_text="Used as the image's alt text.")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to="images/",
        validators=[validate_upload_size],
        help_text="JPEG, PNG or WebP, up to 15 MB. Resized versions are generated on save.",
    )
    # Resized WebP versions, generated from `image` on save (see listings/images.py).
    large = models.ImageField(upload_to="images/large/", blank=True, editable=False)
    card = models.ImageField(upload_to="images/card/", blank=True, editable=False)
    thumb = models.ImageField(upload_to="images/thumb/", blank=True, editable=False)
    default = models.BooleanField(default=False, help_text="Use as the listing's cover image.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_name = self.image.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        regenerate = bool(self.image) and (
            self.image.name != self._source_name or not self.has_derivatives
        )
        super().save(*args, **kwargs)
        if regenerate:
            # The original is in storage now, under its final name.
            self.generate_derivatives()
            super().save(update_fields=list(SIZES))
        self._source_name = self.image.name

    @property
    def has_derivatives(self):
        return all(getattr(self, size) for size in SIZES)

    @property
    def large_url(self):
        return (self.large or self.image).url

    @property
    def card_url(self):
        return (self.card or self.image).url

    @property
    def thumb_url(self):
        return (self.thumb or self.image).url

    def generate_derivatives(self):
        """(Re)build the resized versions from the original; old files are removed."""
        with self.image.open("rb") as source:
            for size in SIZES:
                field = getattr(self, size)
                old_name = field.name
                field.save(
                    derivative_name(self.image.name, size),
                    make_derivative(source, size),
                    save=False,
                )
                if old_name and old_name != field.name:
                    field.storage.delete(old_name)


@receiver(post_delete, sender=Image)
def delete_image_files(sender, instance, **kwargs):
    """Remove the upload and its derivatives from storage when an Image row is deleted."""
    for field in (instance.image, instance.large, instance.card, instance.thumb):
        if field.name:
            field.storage.delete(field.name)


class Contact(models.Model):
    contact_id = models.AutoField(db_column="id", primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        help_text="The property this inquiry was sent from, if any.",
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return f"{self.subject} ({self.email})"


class WebsiteInfo(models.Model):
    info_id = models.AutoField(db_column="id", primary_key=True)
    website_name = models.CharField(max_length=255, default="Real Estate Website")
    business_location = models.CharField(max_length=255, default="Lebanon")
    # Contact & socials
    email = models.EmailField(max_length=254, default="test@example.com")
    phone_number = models.CharField(max_length=255, default="+1 555 634 777")
    whatsapp_number = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text=(
            "Number with country code, e.g. +961 70 123 456. "
            "Leave empty to hide the WhatsApp buttons."
        ),
    )
    facebook_link = models.URLField(max_length=255, default="https://facebook.com/example")
    instagram_link = models.URLField(max_length=255, default="https://instagram.com/example")
    linkedin_link = models.URLField(max_length=255, default="https://linked.in/example")
    # Home page hero
    hero_tagline = models.CharField(
        max_length=80,
        blank=True,
        default="Invest without limits",
        help_text="Small label above the headline. Leave empty to hide it.",
    )
    hero_title = models.CharField(
        max_length=160, default="Premier real estate, from vacant land to your future home"
    )
    hero_subtitle = models.CharField(
        max_length=255, blank=True, default="Hand-picked properties for sale across Lebanon."
    )
    # About us
    about_headline = models.CharField(
        max_length=160,
        default="The best investment on earth is earth",
        help_text="Large heading at the top of the About page.",
    )
    about_us = models.TextField(default="About us info")
    properties_count = models.IntegerField(default=0)
    cities_count = models.IntegerField(default=0)
    offices_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "website info"
        verbose_name_plural = "website info"

    def __str__(self):
        return self.website_name

    @property
    def whatsapp_digits(self):
        """The WhatsApp number as wa.me expects it: digits only, no plus or spaces."""
        return "".join(char for char in self.whatsapp_number if char.isdigit())
