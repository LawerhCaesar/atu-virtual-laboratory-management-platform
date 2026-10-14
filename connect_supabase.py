"""Run a Django command against the project's Supabase database.

Defaults to a read-only readiness check. The password is prompted privately
and passed only to the child process environment, never written to disk.
"""
import getpass
import os
from pathlib import Path
import subprocess
import sys


def main():
    environment = os.environ.copy()
    environment.update(
        POSTGRES_HOST="aws-0-us-east-2.pooler.supabase.com",
        POSTGRES_PORT="5432",
        POSTGRES_DB="postgres",
        POSTGRES_USER="postgres.puogbfavrwfmbmgcwleb",
        POSTGRES_SSLMODE="require",
    )
    password = getpass.getpass("Supabase database password (hidden): ")
    if not password:
        sys.exit("A database password is required.")
    environment["POSTGRES_PASSWORD"] = password
    command = sys.argv[1:] or ["check_database", "--require-postgresql"]
    project = Path(__file__).resolve().parent
    return subprocess.call(
        [sys.executable, str(project / "manage.py"), *command],
        env=environment,
        cwd=project,
    )


if __name__ == "__main__":
    sys.exit(main())
