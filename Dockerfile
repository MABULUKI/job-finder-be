FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production
ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copy project
COPY . /app/

# Create static and media directories
RUN mkdir -p /app/static /app/media

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app

# Set up startup script as root
USER root
RUN printf '#!/bin/bash\n\
echo "Applying database migrations..."\n\
python manage.py migrate\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
echo "Starting Gunicorn..."\n\
exec gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3\n' > /app/start.sh

RUN chmod +x /app/start.sh

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Start the application
CMD ["/bin/bash", "/app/start.sh"]