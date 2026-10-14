# Render staging deployment

This profile runs one paid Render Python web service in Ohio with the existing
Supabase session pooler and a 1 GB persistent disk for private evidence files.
It does not create a Render database. Review the current service and disk cost
in Render before applying the Blueprint.

## Create the staging service

1. Sign in at https://dashboard.render.com/ and choose **New → Blueprint**.
2. Connect the private GitHub repository
   `LawerhCaesar/atu-virtual-laboratory-management-platform`. Grant Render access
   to this repository when prompted.
3. Select `main` and the root `render.yaml` file.
4. Enter the current Supabase database password in Render's protected
   `POSTGRES_PASSWORD` field. Keep passwords out of GitHub and chat.
5. Review the paid service, Ohio region and 1 GB disk, then apply the Blueprint.

Render generates the application secret. Its exact assigned hostname is used
for allowed hosts and HTTPS CSRF origins. Automatic deploys are off: deploy
tested commits manually until staging QA is complete.

## What deployment does

The build installs the Python dependencies and collects the committed static
assets. Startup checks production configuration, the writable evidence disk
and PostgreSQL connectivity. It creates the `atu_staging` schema if absent,
applies Django migrations there and verifies existing evidence references
before starting Gunicorn on Render's assigned port. These database changes
happen only when the service is started, not during local preparation.

The schema is deliberately separate from `public`. Do not add `atu_staging`
to Supabase's exposed API schemas or grant its tables to `anon` or
`authenticated`. The browser uses Django authentication; Supabase Auth and
the Data API are not required. Existing local SQLite records and uploads are
not transferred automatically.

The supplied Supabase `postgres.<project-ref>` connection is an administrative
credential. It can bootstrap this isolated staging schema, but a dedicated
application database role and reviewed grants are still required before
institutional production use. Use synthetic data during staging QA.

Readiness at `/health/ready/` returns 200 only after a successful database
query; database errors produce a generic 503. HTTPS redirection remains on
for normal application routes, with secure session and CSRF cookies. Evidence
stays under the persistent disk and is served through permission-checked
Django download views.

## First administrator and QA

After Render reports **Live**, open its Shell and run:

```bash
python manage.py bootstrap_admin --email YOUR_EMAIL --full-name "Platform Administrator"
```

Enter a temporary password at the hidden prompt. The first login forces a
password change. If Shell cannot provide an interactive prompt, temporarily
set `ATU_ADMIN_EMAIL`, `ATU_ADMIN_FULL_NAME` and `ATU_ADMIN_PASSWORD` in Render,
run `python manage.py bootstrap_admin --no-input`, then remove those variables
after success. Do not put the password in a command argument.

Set up synthetic academic records and student/lecturer accounts through the
protected management screens. Verify registration, approval, allocation,
task publication, upload/download ownership, assessment and result release.
Restart or redeploy once and confirm the evidence file survives and remains
protected. The local `seed_demo_data` command is disabled under production
settings and must not be enabled by switching staging to debug mode.

Before broader release, verify database and evidence backups together,
perform a restore rehearsal and test the actual demonstration integration.
With one attached disk, deploys involve a brief interruption. Back up both
the `atu_staging` schema and evidence files before schema-changing releases.

If Supabase network restrictions are enabled, allow Render's documented
outbound ranges for this service. On connection or startup failure, inspect
Render logs without copying secret environment values into support messages.

## Custom domains

Keep the default `onrender.com` URL for initial QA. If adding a custom domain,
set `DJANGO_ALLOWED_HOSTS` to a comma-separated list containing that domain and
the Render hostname, and `DJANGO_CSRF_TRUSTED_ORIGINS` to their explicit HTTPS
origins. Include any domain Render uses for its health-check Host header.

## References

- https://render.com/docs/blueprint-spec
- https://render.com/docs/deploy-django
- https://render.com/docs/disks
- https://render.com/docs/health-checks
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/api/using-custom-schemas
