"""
WSGI config for job_portal_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Add the project directory to the sys.path
app_path = Path(__file__).resolve().parent.parent
sys.path.append(str(app_path))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal_backend.settings')

# Get the WSGI application
application = get_wsgi_application()

# For Gunicorn
app = application
