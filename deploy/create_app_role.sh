#!/bin/sh
# Runs once for a NEW PostgreSQL volume. Never modifies an existing installation.
set -eu
if [ "$POSTGRES_USER" = "$ATU_APP_USER" ]; then
    echo "Database bootstrap and application roles must be distinct." >&2
    exit 1
fi
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 --quiet <<'SQL'
\getenv app_user ATU_APP_USER
\getenv app_password ATU_APP_PASSWORD
\getenv app_database POSTGRES_DB
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION', :'app_user', :'app_password')
\gexec
SELECT format('ALTER DATABASE %I OWNER TO %I', :'app_database', :'app_user')
\gexec
SQL
