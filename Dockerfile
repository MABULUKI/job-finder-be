FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production
ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copy project
COPY . /app/

# Create static and media directories
RUN mkdir -p /app/static /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Run as non-root user for better security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Create a startup script
USER root
RUN echo '#!/bin/bash\n\
# Apply database migrations\necho "Applying database migrations..."\npython manage.py migrate\n\
# Collect static files\necho "Collecting static files..."\npython manage.py collectstatic --noinput\n\
# Start Gunicorn\necho "Starting Gunicorn..."\nexec gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3' > /app/start.sh

RUN chmod +x /app/start.sh
USER appuser

# Start the application
CMD ["/bin/bash", "/app/start.sh"]
