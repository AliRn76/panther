import logging
from logging.config import dictConfig
from pathlib import Path

from pydantic import BaseModel

from panther.configs import config

LOGS_DIR = config['base_dir'] / 'logs'


class LogConfig(BaseModel):
    """Logging configuration to be set for the server."""

    LOGGER_NAME: str = 'panther-logger'
    DEFAULT_LOG_FORMAT: str = '%(levelprefix)s | %(asctime)s | %(message)s'
    FILE_LOG_FORMAT: str = '%(asctime)s | %(message)s'
    LOG_LEVEL: str = 'DEBUG'
    MAX_FILE_SIZE: int = 1024 * 1024 * 100  # 100 MB

    version: int = 1
    disable_existing_loggers: bool = False

    formatters: dict = {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': DEFAULT_LOG_FORMAT,
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'file_formatter': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': FILE_LOG_FORMAT,
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    }
    handlers: dict = {
        'monitoring_file': {
            'formatter': 'file_formatter',
            'filename': LOGS_DIR / 'monitoring.log',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': MAX_FILE_SIZE,  # 100 MB,
            'backupCount': 3,
        },
        'query_file': {
            'formatter': 'file_formatter',
            'filename': LOGS_DIR / 'query.log',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': MAX_FILE_SIZE,  # 100 MB,
            'backupCount': 3,
        },
        'file': {
            'formatter': 'file_formatter',
            'filename': LOGS_DIR / 'main.log',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': MAX_FILE_SIZE,  # 100 MB,
            'backupCount': 3,
        },
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    }
    loggers: dict = {
        'panther': {
            'handlers': ['default', 'file'],
            'level': LOG_LEVEL,
        },
        'monitoring': {
            'handlers': ['monitoring_file'],
            'level': LOG_LEVEL,
        },
        'query': {
            'handlers': ['default', 'query_file'],
            'level': LOG_LEVEL,
        },
    }


try:
    dictConfig(LogConfig().model_dump())
except ValueError:
    LOGS_DIR = config['base_dir'] / 'logs'
    Path(LOGS_DIR).mkdir(exist_ok=True)


logger = logging.getLogger('panther')
query_logger = logging.getLogger('query')
monitoring_logger = logging.getLogger('monitoring')
