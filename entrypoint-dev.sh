#!/bin/sh

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@gmail.com \
DJANGO_SUPERUSER_PASSWORD=password \
python manage.py createsuperuser --noinput

# Start development server
echo "Starting development server..."
exec python manage.py runserver 0.0.0.0:8000
