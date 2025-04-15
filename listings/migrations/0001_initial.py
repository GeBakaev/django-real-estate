from django.db import migrations, models
import django.db.models.deletion
import geoposition.fields
import os


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "__first__"),
    ]

    # Create First Web Info
    def create_website_info(apps, schema_editor):
        WebsiteInfo = apps.get_model("listings", "WebsiteInfo")
        WebsiteInfo.objects.create()

    def create_default_admin(apps, schema_editor):
        User = apps.get_model("auth", "User")

        # Get credentials from environment variables with fallback defaults
        admin_username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        admin_email = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com")
        admin_password = os.environ.get("DJANGO_ADMIN_PASSWORD", "admin123")

        if not User.objects.filter(username=admin_username).exists():
            admin = User.objects.create_superuser(
                username=admin_username, email=admin_email, password=admin_password
            )
            admin.save()

    operations = [
        migrations.CreateModel(
            name="Listing",
            fields=[
                (
                    "listing_id",
                    models.AutoField(db_column="id", primary_key=True, serialize=False),
                ),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(default="None", max_length=200, unique=True)),
                ("price", models.IntegerField(default=0)),
                ("area", models.IntegerField(default=0)),
                ("description", models.TextField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(0, "Draft"), (1, "Publish")], default=0
                    ),
                ),
                ("location", models.CharField(max_length=200)),
            ],
            options={
                "ordering": ["-created_on"],
            },
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "contact_id",
                    models.AutoField(db_column="id", primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("created_time", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="GeoPosition",
            fields=[
                (
                    "id",
                    models.AutoField(db_column="id", primary_key=True, serialize=False),
                ),
                ("position", geoposition.fields.GeopositionField(max_length=42)),
                (
                    "listing",
                    models.OneToOneField(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fkListingID",
                        to="listings.listing",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WebsiteInfo",
            fields=[
                (
                    "info_id",
                    models.AutoField(db_column="id", primary_key=True, serialize=False),
                ),
                (
                    "website_name",
                    models.CharField(default="Real Estate Website", max_length=255),
                ),
                (
                    "business_location",
                    models.CharField(default="Lebanon", max_length=255),
                ),
                (
                    "email",
                    models.EmailField(default="test@example.com", max_length=254),
                ),
                (
                    "phone_number",
                    models.CharField(default="+1 555 634 777", max_length=255),
                ),
                (
                    "facebook_link",
                    models.URLField(
                        default="https://facebook.com/example", max_length=255
                    ),
                ),
                (
                    "instagram_link",
                    models.URLField(
                        default="https://instagram.com/example", max_length=255
                    ),
                ),
                (
                    "linkedin_link",
                    models.URLField(
                        default="https://linked.in/example", max_length=255
                    ),
                ),
                ("about_us", models.TextField(default="About us info")),
                ("properties_count", models.IntegerField(default=0)),
                ("cities_count", models.IntegerField(default=0)),
                ("offices_count", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Image",
            fields=[
                (
                    "image_id",
                    models.AutoField(db_column="id", primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("image", models.ImageField(upload_to="images/")),
                ("default", models.BooleanField(default=False)),
                (
                    "listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fkListingImageID",
                        to="listings.listing",
                    ),
                ),
            ],
        ),
        # Create First Web Info
        migrations.RunPython(create_website_info),
        # Create Default Admin
        migrations.RunPython(create_default_admin),
    ]
