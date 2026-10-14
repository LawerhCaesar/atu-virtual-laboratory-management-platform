"""Static asset build only: never use this module to run the application."""
from .settings import *  # noqa: F403

# collectstatic inherits upload permissions. Static assets must be readable by
# the non-root web process; private evidence retains 0600/0700 at runtime.
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
