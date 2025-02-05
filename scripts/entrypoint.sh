#!/bin/bash

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
    # Add timeout to prevent infinite loop
    TIMEOUT=$((TIMEOUT+1))
    if [ $TIMEOUT -gt 30 ]; then
        echo "Timeout waiting for PostgreSQL"
        exit 1
    fi
done
echo "PostgreSQL started successfully"

# Run migrations
echo "Running Django migrations..."
python manage.py migrate

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"