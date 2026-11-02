from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ListingQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Listing.Status.PUBLISHED)


class Listing(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, "Draft"
        PUBLISHED = 1, "Published"

    listing_id = models.AutoField(db_column="id", primary_key=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="URL identifier. Generated from the title when left blank.",
    )
    price = models.IntegerField(default=0)
    area = models.IntegerField(default=0, help_text="Area in square metres.")
    description = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
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
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

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
    image = models.ImageField(upload_to="images/")
    default = models.BooleanField(default=False, help_text="Use as the listing's cover image.")

    def __str__(self):
        return self.name


class Contact(models.Model):
    contact_id = models.AutoField(db_column="id", primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    message = models.TextField()
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
    facebook_link = models.URLField(max_length=255, default="https://facebook.com/example")
    instagram_link = models.URLField(max_length=255, default="https://instagram.com/example")
    linkedin_link = models.URLField(max_length=255, default="https://linked.in/example")
    # About us
    about_us = models.TextField(default="About us info")
    properties_count = models.IntegerField(default=0)
    cities_count = models.IntegerField(default=0)
    offices_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "website info"
        verbose_name_plural = "website info"

    def __str__(self):
        return self.website_name
