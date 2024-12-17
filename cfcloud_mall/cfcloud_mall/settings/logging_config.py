import os

from cfcloud_mall.libs.loglib import handler

def main_config(log_path):
    logging_main = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters":{
            "verbose": {
                "format": "{asctime} [{levelname}] [{name}] [{module}.{funcName}:{lineno:d}] {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{asctime} [{levelname}] [{name}] {message}",
                "style": "{",
            },
        },
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(log_path, "cfcm.log"),
                "when": "D",
                "interval": 1,
                "backupCount": 30,
                "delay":True,
                "encoding": "utf8",
            },
            "debug_file": {
                "level": "DEBUG",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filters": ["require_debug_true"],
                "formatter": "verbose",
                "filename": os.path.join(log_path, "cfcm-debug.log"),
                "when": "D",
                "interval": 1,
                "backupCount": 10,
                "delay":True,
                "encoding": "utf8",
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(log_path, "cfcm-error.log"),
                "when": "D",
                "interval": 1,
                "backupCount": 60,
                "delay":True,
                "encoding": "utf8",
            },
            "proxy_root": {
                "()": handler.Logging2PynngProxyHandler.get_proxy,
                "proxy_id":"proxy_root",
                "listen_handler_names": ["console","file","error_file"],
                "level": "INFO",
            },
            "proxy_debug": {
                "()": handler.Logging2PynngProxyHandler.get_proxy,
                "proxy_id": "proxy_debug",
                "listen_handler_names": ["console","debug_file"],
                "level": "DEBUG",
            }
        },
        "loggers": {
            "django.db.backends": {
                "level": "DEBUG",
                "filters": ["require_debug_true", ],
                "handlers": ["proxy_debug"],
                "propagate": False,
            },

        },
        "root": {
            "level": "INFO",
            "handlers": ["proxy_root"],
        }
    }
    return logging_main


def worker_config():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            }
        },
        "handlers": {
            "proxy_root": {
                "()": handler.Logging2PynngProxyHandler.get_proxy,
                "proxy_id":"proxy_root",
                "level": "INFO",
            },
            "proxy_debug": {
                "()": handler.Logging2PynngProxyHandler.get_proxy,
                "proxy_id": "proxy_debug",
                "level": "DEBUG",
            }
        },
        "loggers": {
            "django.db.backends": {
                "level": "DEBUG",
                "filters": ["require_debug_true", ],
                "handlers": ["proxy_debug"],
                "propagate": False,
            },

        },
        "root": {
            "level": "INFO",
            "handlers": ["proxy_root"],
        }
    }
    return config