"""Start the single-instance Render staging service after readiness checks."""
import os
from pathlib import Path
import sys
import tempfile

project = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.render_settings")


def main():
    import django

    django.setup()
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connection

    if settings.DEBUG or connection.vendor != "postgresql":
        sys.exit("Render staging requires production settings and PostgreSQL.")
    schema = os.environ.get("POSTGRES_SCHEMA")
    if schema != "atu_staging":
        sys.exit("Render staging requires the isolated atu_staging schema.")
    call_command("check", deploy=True, fail_level="ERROR")
    media = Path(settings.MEDIA_ROOT)
    media.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Check the mounted disk before migrating or accepting uploads.
    with tempfile.TemporaryFile(dir=media) as probe:
        probe.write(b"storage readiness")
        probe.flush()
    call_command("check_database", require_postgresql=True)
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {connection.ops.quote_name(schema)}")
    call_command("migrate", interactive=False)
    call_command("verify_evidence_storage")
    connection.close()
    os.execv(sys.executable, [
        sys.executable, "-m", "gunicorn", "config.wsgi:application",
        "--bind", f"0.0.0.0:{os.environ.get('PORT', '10000')}",
        "--workers", "2", "--threads", "2", "--timeout", "60",
        "--access-logfile", "-", "--error-logfile", "-",
        "--access-logformat", "%(m)s %(U)s %(s)s %(L)s",
    ])


if __name__ == "__main__":
    main()
