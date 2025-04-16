# Django Libs
from django.db import models
from django.utils.text import slugify

# Django Geoposition-2
from geoposition.fields import GeopositionField


STATUS = ((0, "Draft"), (1, "Publish"))


# Listing Model
class Listing(models.Model):
    listing_id = models.AutoField(db_column="id", primary_key=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, default="None")
    price = models.IntegerField(default=0)
    area = models.IntegerField(default=0)
    description = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)
    location = models.CharField(max_length=200)
    position = GeopositionField(default="0, 0")

    class Meta:
        ordering = ["-created_on"]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


# Image Model
class Image(models.Model):
    image_id = models.AutoField(db_column="id", primary_key=True)
    name = models.CharField(max_length=255)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="fkListingImageID"
    )
    image = models.ImageField(upload_to="images/")
    default = models.BooleanField(default=False)


# Contact Model
class Contact(models.Model):
    contact_id = models.AutoField(db_column="id", primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_time = models.DateTimeField(auto_now_add=True)


# Website Info Model
class WebsiteInfo(models.Model):
    info_id = models.AutoField(db_column="id", primary_key=True)
    website_name = models.CharField(max_length=255, default="Real Estate Website")
    business_location = models.CharField(max_length=255, default="Lebanon")
    # Socials
    email = models.EmailField(max_length=254, default="test@example.com")
    phone_number = models.CharField(max_length=255, default="+1 555 634 777")
    facebook_link = models.URLField(
        max_length=255, default="https://facebook.com/example"
    )
    instagram_link = models.URLField(
        max_length=255, default="https://instagram.com/example"
    )
    linkedin_link = models.URLField(max_length=255, default="https://linked.in/example")
    # About Us
    about_us = models.TextField(default="About us info")
    properties_count = models.IntegerField(default=0)
    cities_count = models.IntegerField(default=0)
    offices_count = models.IntegerField(default=0)


# UTILS
# Get Image Helper Function
def get_image_filename(instance, filename):
    title = instance.listing.title
    slug = slugify(title)
    return "post_images/%s-%s" % (slug, filename)
