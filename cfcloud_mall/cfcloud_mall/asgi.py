"""
ASGI config for cfcloud_mall project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from cfcloud_mall.libs import apputil

app_env = os.getenv('APP_ENV', 'prod')
# 装载环境变量配置
apputil.load_env(app_env)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'cfcloud_mall.settings.{app_env}')

application = get_asgi_application()
