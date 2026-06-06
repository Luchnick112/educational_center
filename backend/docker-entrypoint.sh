#!/bin/sh
set -e

python - <<'PY'
import os
import time

import psycopg

host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
dbname = os.environ.get("POSTGRES_DB", "educational_center")
user = os.environ.get("POSTGRES_USER", "educational_center")
password = os.environ.get("POSTGRES_PASSWORD", "educational_center")

deadline = time.time() + 60
last_error = None

while time.time() < deadline:
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=3,
        ):
            print("PostgreSQL is ready.")
            break
    except Exception as exc:
        last_error = exc
        print(f"Waiting for PostgreSQL at {host}:{port}...")
        time.sleep(2)
else:
    raise SystemExit(f"PostgreSQL is not available: {last_error}")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
