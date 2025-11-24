#!/bin/bash
# Description: 
#     Docker entrypoint script for PAKTON API service.
#     Runs Alembic database migrations before starting the application.
#     
# Author: Raptopoulos Petros [petrosrapto@gmail.com]
# Date  : 2025/11/23

set -e

echo "Starting PAKTON API entrypoint..."

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
timeout=30
counter=0

until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER}" 2>/dev/null || [ $counter -eq $timeout ]; do
  counter=$((counter + 1))
  echo "Waiting for PostgreSQL... ($counter/$timeout)"
  sleep 1
done

if [ $counter -eq $timeout ]; then
  echo "Warning: PostgreSQL readiness check timed out, proceeding anyway..."
fi

# Run database migrations
echo "Running Alembic database migrations..."
cd /app/API
alembic upgrade head
echo "Database migrations completed successfully!"

# Set PYTHONPATH so API package can be imported
export PYTHONPATH=/app:$PYTHONPATH

# Execute the main command (passed as arguments to this script)
echo "Starting application: $@"
exec "$@"
