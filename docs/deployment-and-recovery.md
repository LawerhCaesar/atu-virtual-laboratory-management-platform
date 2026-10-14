# Deployment and Recovery Runbook

This runbook is a controlled release checklist, not a claim that the platform has been deployed or evaluated by study participants.

## Deployment prerequisites

- A dedicated host with Docker Compose, DNS for one approved domain, and a valid TLS certificate.
- An approved maintenance window, institutional backup/retention policy, and an identified system administrator.
- Fresh application/database secrets. Keep `.env.production`, TLS private keys and backup files outside version control; restrict them to the administrator.
- A passing PostgreSQL 18/browser CI run and a staging acceptance review. Pin tested container image digests before an institutional release.

Use `compose.yaml` only for local development. It binds HTTP to `127.0.0.1` and intentionally enables development mode. `compose.production.yaml` is a separate, standalone production configuration.

### Configuration

Create `.env.production` using `.env.production.example` as a field guide. Replace all placeholders, set `ATU_DOMAIN`, and set the same exact domain in `DJANGO_ALLOWED_HOSTS` and the HTTPS origin in `DJANGO_CSRF_TRUSTED_ORIGINS`. Generate a unique, random application secret of at least 50 characters. Production startup rejects missing/default configuration and SQLite fallback.

Place the certificate chain and private key in `deploy/tls/fullchain.pem` and `deploy/tls/privkey.pem`. Restrict the key to the host administrator. Certificate renewal must be arranged separately; restart/reload the proxy after renewal.

The production upstream has no published port and is reachable only through the private Docker network. Nginx replaces incoming forwarding headers. Do not enable `DJANGO_TRUST_PROXY_HEADERS` for an application exposed directly to untrusted clients. This follows [Django's proxy-header warning](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header).

Production uses separate database bootstrap and application roles/passwords. Only the database container receives the bootstrap superuser credentials. On a new volume, `create_app_role.sh` creates a database-owning application role without superuser, database-creation, role-creation or replication privileges. The web health probe rejects an elevated application role. Existing volumes need a supervised role/grant migration; initialization scripts do not rerun automatically. Never reuse bootstrap credentials as application credentials.

HSTS subdomain coverage and preload are off by default. Enable them only after verifying HTTPS for every affected subdomain and approving the long-lived policy. A settings-check warning about these optional flags is not a reason to enable them blindly.

### Persistent storage

The PostgreSQL 18 image volume is mounted at `/var/lib/postgresql`, as described in the [Docker PostgreSQL guide](https://docs.docker.com/guides/postgresql/). Existing installations using an older directory layout need a tested migration/restore procedure; do not delete or reinitialize their volumes to make a configuration change work.

Evidence is stored in a separate private media volume. The application runs as UID/GID 10001, newly uploaded files use mode `0600`, and new directories use `0700`. Nginx denies `/media/`; downloads pass through application role/ownership checks. Existing volumes require a supervised ownership review before switching to the non-root image. Do not mount evidence through a public web-server alias or public object-storage bucket.

File extension/content checks are implemented, but malware scanning is not. An institutional release must assess whether a quarantine/scanning service is required. An S3-backed storage adapter is not part of this increment; the current backend remains private local-volume storage.

### Staging launch and checks

Run these only on the intended staging host, after validating the exact project and environment files:

```bash
docker compose --env-file .env.production -f compose.production.yaml config --quiet
docker compose --env-file .env.production -f compose.production.yaml up --build -d
docker compose --env-file .env.production -f compose.production.yaml exec web python manage.py check --deploy
docker compose --env-file .env.production -f compose.production.yaml exec web python manage.py check_database --require-postgresql --require-least-privilege
docker compose --env-file .env.production -f compose.production.yaml exec web python manage.py verify_evidence_storage
```

The one-shot migration service must finish successfully before Gunicorn starts. Bootstrap the first Administrator using the non-public management command in a private administrator terminal; avoid entering a password into shell history. Complete its forced password change before using the dashboard. Never run `seed_demo_data` in production.

Manually verify HTTP-to-HTTPS redirection, domain rejection, certificate validity, secure cookies, CSRF rejection, resource launch/return on the staging domain, protected evidence access, all role workflows, mobile layout, keyboard operation and screen-reader navigation. Verify the proxy rejects bodies over its upload/callback limits. Do not treat automated accessibility scans as full WCAG certification; [Playwright's guidance](https://playwright.dev/docs/accessibility-testing) explicitly includes manual assessment.

Before public exposure, configure and verify institutional login-abuse throttling, monitoring/alerting, dependency-update review and log retention. These operational controls are not implemented by the present application. The CSP is a baseline frame/object/base restriction, with same-origin account forms; it is not a complete nonce-based script policy. Approved external launch redirects must remain functional when extending it.

## Backup procedure

PostgreSQL and evidence must be backed up as a matched set. A database-only backup cannot recover attached files. Use a maintenance window to prevent evidence additions/removals or assessment changes during capture. The [PostgreSQL dump guidance](https://www.postgresql.org/docs/18/backup-dump.html) explains logical dumps and restore compatibility.

The following commands are examples for an administrator operating the already-validated production project. Choose a fresh, explicit backup directory for each capture. No backup operation is run automatically by this repository.

```bash
umask 077
mkdir -p backups
mkdir backups/2026-09-13T120000Z
docker compose --env-file .env.production -f compose.production.yaml stop proxy web
docker compose --env-file .env.production -f compose.production.yaml exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/2026-09-13T120000Z/database.dump
docker compose --env-file .env.production -f compose.production.yaml run --rm --no-deps web tar -czf - -C /app/media . > backups/2026-09-13T120000Z/media.tar.gz
docker compose --env-file .env.production -f compose.production.yaml start web proxy
shasum -a 256 backups/2026-09-13T120000Z/database.dump backups/2026-09-13T120000Z/media.tar.gz
```

Stop if any capture command fails; do not label incomplete files as a successful backup. Restart the services safely even if capture fails. Save the checksums, application revision, PostgreSQL image version, record counts, capture timestamps and operator identity in a restricted manifest. Encrypt the bundle using the institution's approved tooling before off-host transfer. Back up secrets/configuration through a separate restricted recovery process, never inside a public report. Apply retention/deletion only after institutional approval.

## Restore rehearsal

Never test a restore against the live database or its media volume. Use a dedicated recovery host or an explicitly separate Compose project, empty database and new volumes. Verify backup checksums before opening either archive.

1. Build the matching application revision and initialize the isolated PostgreSQL 18 service.
2. Restore the custom-format dump using the PostgreSQL image's `pg_restore`, into the empty database with `--no-owner`. Do not use `--clean` against an existing user database.
3. Restore the media archive into the isolated private media volume, using the application UID/GID and preserving restricted permissions.
4. Run migrations only after confirming the restored schema/revision, then run `check_database --require-postgresql` and `verify_evidence_storage`.
5. Compare pre-backup and restored record counts, check representative protected downloads, and review submission/feedback/result/audit continuity under each role.
6. Record recovery duration, missing-file count, operator and rehearsal outcome as operational evidence. These results are not yet measured by this project.

Institutional recovery-time/recovery-point objectives, backup frequency and retention periods remain decisions for the deployment owner.

## Repeatable verification

```bash
python -m pip install -r requirements-dev.txt
pnpm install --frozen-lockfile --ignore-scripts
pnpm run sync-assets
python -m playwright install chromium
pytest -q
pytest -m e2e tests/e2e -q
```

Browser fixtures use a disposable Django test database and temporary media, block external HTTP resources, and write axe reports under `test-results/accessibility/`. Failures retain screenshots and Playwright traces under `test-results/e2e/`. Use `ATU_BROWSER_CHANNEL=chrome` only when deliberately testing an installed Chrome build; CI uses Playwright's bundled Chromium. The test-only async-safety exception exists solely for serial fixture ORM access and must never be set in a deployment environment.

The CI workflow also runs migrations/tests against a disposable PostgreSQL 18 service and validates the container build and production Compose syntax. A workflow file existing locally is not evidence that a remote CI run passed.
