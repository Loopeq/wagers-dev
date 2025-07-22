#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done
echo "PostgreSQL is up!"


alembic upgrade head

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

