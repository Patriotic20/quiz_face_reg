#!/bin/bash
set -e

cd /app/app

if [ -f "alembic.ini" ]; then
  echo "Running migrations..."
  alembic -c alembic.ini upgrade head
else
  echo "alembic.ini not found, skipping migrations"
fi

echo "Starting application..."
exec python main.py
