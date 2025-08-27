#!/bin/sh

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@gmail.com \
DJANGO_SUPERUSER_PASSWORD=password \
python manage.py createsuperuser --noinput

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 libapi.wsgi:application