import os
import sys
from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.auditlog.services import record_event


class Command(BaseCommand):
    help = "Create the first platform administrator without exposing public admin registration."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=os.getenv("ATU_ADMIN_EMAIL"))
        parser.add_argument("--full-name", default=os.getenv("ATU_ADMIN_FULL_NAME"))
        parser.add_argument("--password", default=os.getenv("ATU_ADMIN_PASSWORD"))
        parser.add_argument("--no-input", action="store_true")

    def handle(self, *args, **options):
        email = options["email"]
        full_name = options["full_name"]
        password = options["password"]
        if email and full_name and not password and not options["no_input"] and sys.stdin.isatty():
            password = getpass("Temporary administrator password: ")
            if password != getpass("Confirm temporary password: "):
                raise CommandError("Passwords did not match.")
        if not all([email, full_name, password]):
            raise CommandError(
                "Provide --email, --full-name and --password, or set the corresponding ATU_ADMIN_* variables."
            )
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError("An account with that email address already exists.")
        try:
            validate_password(password, User(email=email, full_name=full_name))
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        administrator = User.objects.create_superuser(
            email=email,
            full_name=full_name,
            password=password,
            must_change_password=True,
        )
        record_event(action="ADMIN_BOOTSTRAPPED", actor=administrator, target=administrator)
        self.stdout.write(self.style.SUCCESS(f"Administrator created for {administrator.email}."))
