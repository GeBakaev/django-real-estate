import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create the initial admin account from environment variables, once.

    Reads DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_EMAIL and DJANGO_ADMIN_PASSWORD.
    Does nothing if the password is unset or the user already exists, so it is
    safe to run on every container start.
    """

    help = "Create the admin user from DJANGO_ADMIN_* env vars if it does not exist."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        email = os.environ.get("DJANGO_ADMIN_EMAIL", "")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")

        if not password:
            self.stdout.write("DJANGO_ADMIN_PASSWORD not set; skipping admin creation.")
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Admin user '{username}' already exists.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))
