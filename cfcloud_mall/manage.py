#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from cfcloud_mall.libs import apputil
from cfcloud_mall.libs.loglib import handler


def main():
    """Run administrative tasks."""
    app_env = os.getenv('APP_ENV', 'dev')
    # 装载环境变量配置
    apputil.load_env(app_env)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'cfcloud_mall.settings.{app_env}')
    # 启动日志服务
    if os.environ.get("RUN_MAIN") == "true":
        os.environ["RUN_IN_MAIN_PROCESS"] = "True"
        handler.start_pynng_logging_listener()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
