from django.core.management.base import BaseCommand

from listings.images import SIZES
from listings.models import Image


class Command(BaseCommand):
    help = "Generate the resized versions of listing photos that are missing (all with --force)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Rebuild even if present.")

    def handle(self, *args, force=False, **options):
        done = failed = 0
        for image in Image.objects.iterator():
            if not force and image.has_derivatives:
                continue
            try:
                image.generate_derivatives()
                image.save(update_fields=list(SIZES))
            except (OSError, ValueError) as exc:
                failed += 1
                self.stderr.write(f"Image {image.pk} ({image.image.name}): {exc}")
                continue
            done += 1
        self.stdout.write(f"Generated derivatives for {done} image(s), {failed} failed.")
