#!/bin/bash
set -e

echo "Running migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Starting application..."
exec python /app/main.py
