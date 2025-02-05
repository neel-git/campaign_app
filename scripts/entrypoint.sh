#!/bin/sh

echo "Starting deployment process..."

# Function to test PostgreSQL connection
postgres_ready() {
    python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${DB_NAME}",
        user="${DB_USER}",
        password="${DB_PASSWORD}",
        host="${DB_HOST}",
        port="${DB_PORT}"
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
}

# Wait for PostgreSQL to become available
until postgres_ready; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up and running!"

# Run migrations
echo "Running Django migrations..."
python manage.py migrate

echo "Running Alembic migrations..."
alembic upgrade head

# Start application
echo "Starting application..."
exec "$@"