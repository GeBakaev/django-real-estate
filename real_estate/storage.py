from django.contrib.staticfiles import storage


class ManifestStaticFilesStorage(storage.ManifestStaticFilesStorage):
    """Manifest storage that degrades to plain filenames when nothing has been collected.

    Django's version raises for any file missing from the manifest, which would break the
    test suite and a fresh checkout run with DEBUG=0 before `collectstatic`. In production
    the entrypoint always collects first, so there every file is hashed as usual.
    """

    manifest_strict = False

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            return name
