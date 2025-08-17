#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done
echo "PostgreSQL is up!"


alembic upgrade head

if [ "$DEV" = "1" ]; then
    echo "Starting in development mode with Uvicorn..."
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting in production mode with Gunicorn..."
    gunicorn src.main:app \
      --workers 4 \
      --worker-class uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:8000 \
      --log-level error
fi