#!/bin/bash
set -e

echo "Starting E-Commerce Platform initialization..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "$DB_HOST" -p 5432 -U "$DB_USER"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run database initialization
echo "Initializing database..."
python -c "
from src.main import db, app
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Start the application
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 src.main:app