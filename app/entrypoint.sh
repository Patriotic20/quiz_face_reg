#!/bin/bash
set -e

# Если ваши миграции (папка alembic) лежат в подпапке /app/app
# то может потребоваться переход: cd /app
echo "Running migrations..."
alembic upgrade head

# Выполняем команду, переданную в CMD (запуск python)
exec "$@"