from django.core.management.base import BaseCommand, CommandError

from apps.practicals.models import EvidenceFile


class Command(BaseCommand):
    help = "Read-only recovery check for all evidence-file references; emits counts, not private paths."

    def handle(self, *args, **options):
        checked = missing = 0
        for evidence in EvidenceFile.objects.iterator():
            checked += 1
            if not evidence.file.name or not evidence.file.storage.exists(evidence.file.name):
                missing += 1
        if missing:
            raise CommandError(f"Evidence recovery check failed: {missing} missing of {checked} references.")
        self.stdout.write(f"Evidence storage verified: {checked} references, 0 missing.")
