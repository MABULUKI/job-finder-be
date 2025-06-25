FROM python:3.11-slim-bullseye

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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

# Copy project files
COPY . .

# Static/media dirs
RUN mkdir -p /app/static /app/media

# Start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Let Render know the port is open (but don't hardcode it!)
EXPOSE 8000

# Run start script
CMD ["/bin/bash", "/app/start.sh"]
