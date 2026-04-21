#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set. Aborting."
  exit 1
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "Migrations and collectstatic completed."
