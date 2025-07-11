from datetime import timedelta
from pathlib import Path
from unittest import TestCase

import jinja2

from panther import Panther
from panther.app import GenericAPI
from panther.authentications import CookieJWTAuthentication, QueryParamJWTAuthentication
from panther.base_websocket import WebsocketConnections
from panther.configs import JWTConfig, config
from panther.db import Model
from panther.db.connections import PantherDBConnection
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.events import Event
from panther.middlewares.monitoring import MonitoringMiddleware, WebsocketMonitoringMiddleware
from panther.throttling import Throttle
from panther.utils import generate_secret_key
from panther.websocket import GenericWebsocket


class User(Model):
    pass


class Book(Model):
    pass


class Author(Model):
    pass


class DummyAPI(GenericAPI):
    pass


class DummyWS(GenericWebsocket):
    pass


@Event.startup
def my_startup1():
    pass


@Event.startup
def my_startup2():
    pass


@Event.shutdown
def my_shutdown1():
    pass


@Event.shutdown
def my_shutdown2():
    pass


class TestConfig(TestCase):
    def test_loading_known_configs(self):
        global \
            BASE_DIR, \
            MONITORING, \
            LOG_QUERIES, \
            THROTTLING, \
            SECRET_KEY, \
            MIDDLEWARES, \
            HTTP_MIDDLEWARES, \
            WS_MIDDLEWARES, \
            USER_MODEL, \
            AUTHENTICATION, \
            WS_AUTHENTICATION, \
            JWT_CONFIG, \
            MODELS, \
            FLAT_URLS, \
            URLS, \
            WEBSOCKET_CONNECTIONS, \
            BACKGROUND_TASKS, \
            HAS_WS, \
            TIMEZONE, \
            TEMPLATES_DIR, \
            JINJA_ENVIRONMENT, \
            AUTO_REFORMAT, \
            QUERY_ENGINE, \
            DATABASE

        # MIDDLEWARES
        MIDDLEWARES = ['panther.middlewares.monitoring.MonitoringMiddleware']
        WS_MIDDLEWARES = ['panther.middlewares.monitoring.WebsocketMonitoringMiddleware']
        LOG_QUERIES = True
        throttle = Throttle(rate=10, duration=timedelta(seconds=10))
        THROTTLING = throttle
        new_secret_key = generate_secret_key()
        SECRET_KEY = new_secret_key
        USER_MODEL = 'tests.test_config.User'
        AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
        WS_AUTHENTICATION = 'panther.authentications.CookieJWTAuthentication'
        JWT_CONFIG = {'life_time': timedelta(seconds=20)}
        BACKGROUND_TASKS = True
        TIMEZONE = 'Asia/Tehran'
        TEMPLATES_DIR = 'templates/'
        AUTO_REFORMAT = True
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.PantherDBConnection',
            },
        }

        # Check before loading configs.
        # assert Path() == config.BASE_DIR
        assert config.MONITORING is False
        assert config.LOG_QUERIES is False
        assert config.THROTTLING is None
        assert config.SECRET_KEY is None
        assert config.HTTP_MIDDLEWARES == []
        assert config.WS_MIDDLEWARES == []
        assert config.USER_MODEL is None
        assert config.AUTHENTICATION is None
        assert config.WS_AUTHENTICATION is None
        assert config.JWT_CONFIG is None
        assert [User, Book, Author] == config.MODELS  # This is ok.
        assert config.FLAT_URLS == {}
        assert config.URLS == {}
        assert config.WEBSOCKET_CONNECTIONS is None
        assert config.BACKGROUND_TASKS is False
        assert config.HAS_WS is True
        assert config.TIMEZONE == 'UTC'
        assert config.TEMPLATES_DIR == '.'
        assert config.JINJA_ENVIRONMENT is None
        assert config.AUTO_REFORMAT is False
        assert config.QUERY_ENGINE is None
        assert config.DATABASE is None

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={'dummy': DummyAPI, 'ws': DummyWS})

        # Check vars()
        assert [*config.vars().keys()] == [
            'BASE_DIR',
            'MONITORING',
            'LOG_QUERIES',
            'SECRET_KEY',
            'HTTP_MIDDLEWARES',
            'WS_MIDDLEWARES',
            'USER_MODEL',
            'AUTHENTICATION',
            'WS_AUTHENTICATION',
            'JWT_CONFIG',
            'MODELS',
            'FLAT_URLS',
            'URLS',
            'WEBSOCKET_CONNECTIONS',
            'BACKGROUND_TASKS',
            'HAS_WS',
            'TIMEZONE',
            'TEMPLATES_DIR',
            'JINJA_ENVIRONMENT',
            'AUTO_REFORMAT',
            'QUERY_ENGINE',
            'DATABASE',
            'THROTTLING',
            'MIDDLEWARES',
        ]

        # Check after loading configs.
        assert Path.cwd() == config.BASE_DIR
        assert config.MONITORING is True
        assert config.LOG_QUERIES is True
        assert throttle == config.THROTTLING
        assert new_secret_key == config.SECRET_KEY
        assert [MonitoringMiddleware] == config.HTTP_MIDDLEWARES
        assert [WebsocketMonitoringMiddleware] == config.WS_MIDDLEWARES
        assert config.USER_MODEL is User
        assert config.AUTHENTICATION is QueryParamJWTAuthentication
        assert config.WS_AUTHENTICATION is CookieJWTAuthentication
        assert JWTConfig(key=new_secret_key, algorithm='HS256', life_time=20, refresh_life_time=40) == config.JWT_CONFIG
        assert [User, Book, Author] == config.MODELS
        assert {'dummy/': DummyAPI, 'ws/': DummyWS} == config.FLAT_URLS
        assert {'dummy': DummyAPI, 'ws': DummyWS} == config.URLS
        assert isinstance(config.WEBSOCKET_CONNECTIONS, WebsocketConnections)
        assert config.BACKGROUND_TASKS is True
        assert config.HAS_WS is True
        assert config.TIMEZONE == 'Asia/Tehran'
        assert config.TEMPLATES_DIR == 'templates/'
        assert isinstance(config.JINJA_ENVIRONMENT, jinja2.environment.Environment)
        assert config.AUTO_REFORMAT is True
        assert config.QUERY_ENGINE is BasePantherDBQuery
        assert isinstance(config.DATABASE, PantherDBConnection)

    def test_loading_unknown_configs(self):
        global CUSTOM_KEY
        CUSTOM_KEY = 'I am custom'

        # Check before loading configs.
        assert config.CUSTOM_KEY is None

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={})

        # Check after loading configs.
        assert config.CUSTOM_KEY == 'I am custom'

    def test_loading_unknown_configs_invalid_name(self):
        global CUSTOM_key
        CUSTOM_key = 'I am custom'

        # Check before loading configs.
        assert config.CUSTOM_key is None

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={})

        # Check after loading configs.
        assert config.CUSTOM_key is None

    def test_refresh_configs(self):
        global \
            BASE_DIR, \
            MONITORING, \
            LOG_QUERIES, \
            THROTTLING, \
            SECRET_KEY, \
            MIDDLEWARES, \
            HTTP_MIDDLEWARES, \
            WS_MIDDLEWARES, \
            USER_MODEL, \
            AUTHENTICATION, \
            WS_AUTHENTICATION, \
            JWT_CONFIG, \
            MODELS, \
            FLAT_URLS, \
            URLS, \
            WEBSOCKET_CONNECTIONS, \
            BACKGROUND_TASKS, \
            HAS_WS, \
            TIMEZONE, \
            TEMPLATES_DIR, \
            JINJA_ENVIRONMENT, \
            AUTO_REFORMAT, \
            QUERY_ENGINE, \
            DATABASE

        # MIDDLEWARES
        MIDDLEWARES = ['panther.middlewares.monitoring.MonitoringMiddleware']
        WS_MIDDLEWARES = ['panther.middlewares.monitoring.WebsocketMonitoringMiddleware']
        LOG_QUERIES = True
        throttle = Throttle(rate=10, duration=timedelta(seconds=10))
        THROTTLING = throttle
        new_secret_key = generate_secret_key()
        SECRET_KEY = new_secret_key
        USER_MODEL = 'tests.test_config.User'
        AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
        WS_AUTHENTICATION = 'panther.authentications.CookieJWTAuthentication'
        JWT_CONFIG = {'life_time': timedelta(seconds=20)}
        BACKGROUND_TASKS = True
        TIMEZONE = 'Asia/Tehran'
        TEMPLATES_DIR = 'templates/'
        AUTO_REFORMAT = True
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.PantherDBConnection',
            },
        }

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={'dummy': DummyAPI, 'ws': DummyWS})
        config.refresh()

        assert Path() == config.BASE_DIR
        assert config.MONITORING is False
        assert config.LOG_QUERIES is False
        assert config.THROTTLING is None
        assert config.SECRET_KEY is None
        assert config.HTTP_MIDDLEWARES == []
        assert config.WS_MIDDLEWARES == []
        assert config.USER_MODEL is None
        assert config.AUTHENTICATION is None
        assert config.WS_AUTHENTICATION is None
        assert config.JWT_CONFIG is None
        assert config.MODELS == []
        assert config.FLAT_URLS == {}
        assert config.URLS == {}
        assert config.WEBSOCKET_CONNECTIONS is None
        assert config.BACKGROUND_TASKS is False
        assert config.HAS_WS is False
        assert config.TIMEZONE == 'UTC'
        assert config.TEMPLATES_DIR == '.'
        assert config.JINJA_ENVIRONMENT is None
        assert config.AUTO_REFORMAT is False
        assert config.QUERY_ENGINE is None
        assert config.DATABASE is None

    def test_loading_unknown_config_types(self):
        global CUSTOM_INT, CUSTOM_LIST, CUSTOM_DICT, CUSTOM_BOOL
        CUSTOM_INT = 5
        CUSTOM_LIST = [1, 2]
        CUSTOM_DICT = {'name': 'ali'}
        CUSTOM_BOOL = True

        # Check before loading configs.
        assert config.CUSTOM_INT is None
        assert config.CUSTOM_LIST is None
        assert config.CUSTOM_DICT is None
        assert config.CUSTOM_BOOL is None

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={})

        # Check after loading configs.
        assert config.CUSTOM_INT == 5
        assert config.CUSTOM_LIST == [1, 2]
        assert config.CUSTOM_DICT == {'name': 'ali'}
        assert config.CUSTOM_BOOL is True
