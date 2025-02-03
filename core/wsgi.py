"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from utils.config_loader import ConfigurationLoader

config = ConfigurationLoader()
settings = config.load_config()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Set environment variables from configuration
for key,value in settings.get('environment',{}).items():
    os.environ[key] = str(value)

application = get_wsgi_application()
