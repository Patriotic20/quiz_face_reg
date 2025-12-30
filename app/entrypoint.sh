#!/bin/bash
set -e

if [ -f "/app/app/alembic.ini" ]; then
  echo "Running migrations..."
  uv run alembic upgrade head
fi

echo "Starting application..."
exec python /app/app/main.py
