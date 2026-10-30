from decimal import Decimal, InvalidOperation

import django.core.validators
from django.db import migrations, models


def parse_position(value):
    """Split a django-geoposition string ("lat,lng" or "lat, lng") into Decimals.

    Returns (None, None) for empty, malformed or the "0, 0" placeholder.
    """
    if not value:
        return None, None
    parts = [p.strip() for p in str(value).split(",")]
    if len(parts) != 2:
        return None, None
    try:
        lat, lng = Decimal(parts[0]), Decimal(parts[1])
    except InvalidOperation:
        return None, None
    if lat == 0 and lng == 0:
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, None
    return lat, lng


def forwards(apps, schema_editor):
    Listing = apps.get_model("listings", "Listing")
    for listing in Listing.objects.all().iterator():
        lat, lng = parse_position(listing.position)
        if lat is not None:
            listing.latitude = lat
            listing.longitude = lng
            listing.save(update_fields=["latitude", "longitude"])


def backwards(apps, schema_editor):
    Listing = apps.get_model("listings", "Listing")
    for listing in Listing.objects.all().iterator():
        if listing.latitude is not None and listing.longitude is not None:
            listing.position = f"{listing.latitude},{listing.longitude}"
        else:
            listing.position = "0, 0"
        listing.save(update_fields=["position"])


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0003_listing_slug_blank_image_related_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-90),
                    django.core.validators.MaxValueValidator(90),
                ],
            ),
        ),
        migrations.AddField(
            model_name="listing",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-180),
                    django.core.validators.MaxValueValidator(180),
                ],
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name="listing",
            name="position",
        ),
    ]
