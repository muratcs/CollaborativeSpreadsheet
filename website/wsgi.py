"""
WSGI config for website project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import spreadsheet.serverclient
from spreadsheet.models import BrowserClient

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")



BrowserClient.objects.all().delete()
s = spreadsheet.serverclient.Server()
s.start()

application = get_wsgi_application()
