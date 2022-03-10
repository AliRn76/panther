import logging.config
from typing import Dict

# TODO: change
LOGGING: Dict = {
    "version": 1,
    "formatters": {
        "standard": {
            "class": "logging.Formatter",
            "format": "%(asctime)s\t%(levelname)s\t%(filename)s\t%(message)s",
            "datefmt": "%d %b %y %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "level": "INFO",
            "filename": "framework.log",
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 500000,
            "backupCount": 4
        }
    },
    "loggers": {
        "__main__": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
