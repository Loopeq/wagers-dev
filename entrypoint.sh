#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done
echo "PostgreSQL is up!"


alembic upgrade head

gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000