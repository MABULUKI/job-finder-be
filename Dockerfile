FROM python:3.11-slim-bullseye

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy app files
COPY . .

# Static/media dirs
RUN mkdir -p /app/static /app/media

# Add a non-root user for better security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose the correct port
EXPOSE 8000

# Start server using environment PORT (Render requires it)
CMD gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3
