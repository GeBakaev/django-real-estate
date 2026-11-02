"""Resized WebP versions of uploaded listing photos."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# name -> (width, height, crop). Cropped sizes are exact; "large" only shrinks to fit.
SIZES = {
    "large": (1600, 1600, False),
    "card": (800, 600, True),
    "thumb": (320, 240, True),
}
QUALITY = {"large": 82, "card": 80, "thumb": 75}


def derivative_name(original_name, size):
    return f"{Path(original_name).stem}-{size}.webp"


def make_derivative(source, size):
    """Return a ContentFile with the resized WebP for ``size``; ``source`` is a file object."""
    width, height, crop = SIZES[size]
    source.seek(0)
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        if image.mode not in ("RGB", "RGBA"):
            keep_alpha = image.mode in ("LA", "PA") or "transparency" in image.info
            image = image.convert("RGBA" if keep_alpha else "RGB")
        if crop:
            image = ImageOps.fit(image, (width, height), Image.LANCZOS)
        else:
            image.thumbnail((width, height), Image.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, "WEBP", quality=QUALITY[size], method=4)
    return ContentFile(buffer.getvalue())
