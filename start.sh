#!/bin/bash

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Start Gunicorn using the correct Render port
exec gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3
