import logging
from pathlib import Path
from panther.configs import config

LOGS_DIR = config.BASE_DIR / 'logs'


class FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, errors=None):
        Path(LOGS_DIR).mkdir(exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode=mode, encoding=encoding, delay=delay, errors=errors)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(levelprefix)s | %(asctime)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'panther_file_formatter': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(asctime)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'panther_file': {
            'formatter': 'panther_file_formatter',
            'filename': LOGS_DIR / 'main.log',
            'class': 'panther.logging.FileHandler',
            'delay': True,
        },
        'monitoring_file': {
            'formatter': 'panther_file_formatter',
            'filename': LOGS_DIR / 'monitoring.log',
            'class': 'panther.logging.FileHandler',
            'delay': True,
        },
        'query_file': {
            'formatter': 'panther_file_formatter',
            'filename': LOGS_DIR / 'query.log',
            'class': 'panther.logging.FileHandler',
            'delay': True,
        },
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'panther': {
            'handlers': ['default', 'panther_file'],
            'level': 'DEBUG',
        },
        'monitoring': {
            'handlers': ['monitoring_file'],
            'level': 'DEBUG',
        },
        'query': {
            'handlers': ['default', 'query_file'],
            'level': 'DEBUG',
        },
    }
}
