"""
开发环境配置文件
"""
import os
from ..libs.loglib import handler
from .base import *
DEBUG = True
# debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_COLLAPSED': True,
    }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str('CACHES.default.LOCATION', ''),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100}# in seconds
        }
    },
    "session": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str('CACHES.session.LOCATION', ''),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
            "SOCKET_TIMEOUT": 5,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100}# in seconds
        }
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"