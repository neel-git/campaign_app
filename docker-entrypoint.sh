#!/bin/sh

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
    sleep 0.1
done
echo "Database is ready!"

echo "Running Django migrations..."
python manage.py migrate

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"