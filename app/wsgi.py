"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application #создаёт WSGI-приложение, совместимое с WSGI-серверами

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings') #DJANGO_SETTINGS_MODULE указывает, где искать настройки проекта/ 'app.settings' это путь к файлу settings.py в приложении app.

application = get_wsgi_application()
