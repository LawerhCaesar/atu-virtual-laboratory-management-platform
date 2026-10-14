from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Read-only database readiness probe; optionally require PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument("--require-postgresql", action="store_true")
        parser.add_argument("--require-least-privilege", action="store_true")

    def handle(self, *args, **options):
        if (options["require_postgresql"] or options["require_least_privilege"]) and connection.vendor != "postgresql":
            raise CommandError("PostgreSQL is required by this deployment probe.")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise CommandError("Database readiness probe failed.")
                if options["require_least_privilege"]:
                    cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication FROM pg_roles WHERE rolname = current_user")
                    privileges = cursor.fetchone()
                    if not privileges or any(privileges):
                        raise CommandError("Application database role must not have elevated privileges.")
        except CommandError:
            raise
        except Exception as exc:
            # Never print DSNs or database exception details in health logs.
            raise CommandError("Database readiness probe failed.") from exc
        self.stdout.write("Database ready.")
