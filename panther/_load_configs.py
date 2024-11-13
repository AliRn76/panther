import logging
import sys
import types
from importlib import import_module
from multiprocessing import Manager

import jinja2

from panther._utils import import_class, check_function_type_endpoint, check_class_type_endpoint
from panther.background_tasks import background_tasks
from panther.base_websocket import WebsocketConnections
from panther.cli.utils import import_error
from panther.configs import JWTConfig, config
from panther.db.connections import redis
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.exceptions import PantherError
from panther.middlewares.base import WebsocketMiddleware, HTTPMiddleware
from panther.panel.urls import urls as panel_urls
from panther.routings import finalize_urls, flatten_urls

__all__ = (
    'load_configs_module',
    'load_redis',
    'load_startup',
    'load_shutdown',
    'load_timezone',
    'load_database',
    'load_secret_key',
    'load_monitoring',
    'load_throttling',
    'load_user_model',
    'load_log_queries',
    'load_middlewares',
    'load_templates_dir',
    'load_auto_reformat',
    'load_background_tasks',
    'load_default_cache_exp',
    'load_authentication_class',
    'load_urls',
    'load_websocket_connections',
    'check_endpoints_inheritance',
)

logger = logging.getLogger('panther')


def load_configs_module(module_name: str, /) -> dict:
    """Read the config file as dict"""
    if module_name:
        _module = sys.modules[module_name]
    else:
        try:
            _module = import_module('core.configs')
        except ModuleNotFoundError:
            raise _exception_handler(field='core/configs.py', error='Not Found')
    return _module.__dict__


def load_redis(_configs: dict, /) -> None:
    if redis_config := _configs.get('REDIS'):
        # Check redis module installation
        try:
            from redis.asyncio import Redis
        except ImportError as e:
            raise import_error(e, package='redis')
        redis_class_path = redis_config.get('class', 'panther.db.connections.RedisConnection')
        redis_class = import_class(redis_class_path)
        # We have to create another dict then pop the 'class' else we can't pass the tests
        args = redis_config.copy()
        args.pop('class', None)
        redis_class(**args, init=True)


def load_startup(_configs: dict, /) -> None:
    if startup := _configs.get('STARTUP'):
        config.STARTUP = import_class(startup)


def load_shutdown(_configs: dict, /) -> None:
    if shutdown := _configs.get('SHUTDOWN'):
        config.SHUTDOWN = import_class(shutdown)


def load_timezone(_configs: dict, /) -> None:
    if timezone := _configs.get('TIMEZONE'):
        config.TIMEZONE = timezone


def load_templates_dir(_configs: dict, /) -> None:
    if templates_dir := _configs.get('TEMPLATES_DIR'):
        config.TEMPLATES_DIR = templates_dir

    if config.TEMPLATES_DIR == '.':
        config.TEMPLATES_DIR = config.BASE_DIR

    config.JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(config.TEMPLATES_DIR))


def load_database(_configs: dict, /) -> None:
    database_config = _configs.get('DATABASE', {})
    if 'engine' in database_config:
        if 'class' not in database_config['engine']:
            raise _exception_handler(field='DATABASE', error=f'`engine["class"]` not found.')

        engine_class_path = database_config['engine']['class']
        engine_class = import_class(engine_class_path)
        # We have to create another dict then pop the 'class' else we can't pass the tests
        args = database_config['engine'].copy()
        args.pop('class')
        config.DATABASE = engine_class(**args)

        if engine_class_path == 'panther.db.connections.PantherDBConnection':
            config.QUERY_ENGINE = BasePantherDBQuery
        elif engine_class_path == 'panther.db.connections.MongoDBConnection':
            config.QUERY_ENGINE = BaseMongoDBQuery

    if 'query' in database_config:
        if config.QUERY_ENGINE:
            logger.warning('`DATABASE.query` has already been filled.')
        config.QUERY_ENGINE = import_class(database_config['query'])


def load_secret_key(_configs: dict, /) -> None:
    if secret_key := _configs.get('SECRET_KEY'):
        config.SECRET_KEY = secret_key.encode()


def load_monitoring(_configs: dict, /) -> None:
    if _configs.get('MONITORING'):
        config.MONITORING = True


def load_throttling(_configs: dict, /) -> None:
    if throttling := _configs.get('THROTTLING'):
        config.THROTTLING = throttling


def load_user_model(_configs: dict, /) -> None:
    config.USER_MODEL = import_class(_configs.get('USER_MODEL', 'panther.db.models.BaseUser'))
    config.MODELS.append(config.USER_MODEL)


def load_log_queries(_configs: dict, /) -> None:
    if _configs.get('LOG_QUERIES'):
        config.LOG_QUERIES = True


def load_middlewares(_configs: dict, /) -> None:
    from panther.middlewares import BaseMiddleware

    middlewares = {'http': [], 'ws': []}

    # Collect Middlewares
    for middleware in _configs.get('MIDDLEWARES') or []:
        if not isinstance(middleware, list | tuple):
            raise _exception_handler(field='MIDDLEWARES', error=f'{middleware} should have 2 part: (path, kwargs)')

        if len(middleware) == 1:
            path = middleware[0]
            data = {}

        elif len(middleware) > 2:
            raise _exception_handler(field='MIDDLEWARES', error=f'{middleware} too many arguments')

        else:
            path, data = middleware

        try:
            middleware_class = import_class(path)
        except (AttributeError, ModuleNotFoundError):
            raise _exception_handler(field='MIDDLEWARES', error=f'{path} is not a valid middleware path')

        if issubclass(middleware_class, BaseMiddleware) is False:
            raise _exception_handler(field='MIDDLEWARES', error='is not a sub class of BaseMiddleware')

        if middleware_class.__bases__[0] in (BaseMiddleware, HTTPMiddleware):
            middlewares['http'].append((middleware_class, data))

        if middleware_class.__bases__[0] in (BaseMiddleware, WebsocketMiddleware):
            middlewares['ws'].append((middleware_class, data))

    config.HTTP_MIDDLEWARES = middlewares['http']
    config.WS_MIDDLEWARES = middlewares['ws']


def load_auto_reformat(_configs: dict, /) -> None:
    if _configs.get('AUTO_REFORMAT'):
        config.AUTO_REFORMAT = True


def load_background_tasks(_configs: dict, /) -> None:
    if _configs.get('BACKGROUND_TASKS'):
        config.BACKGROUND_TASKS = True
        background_tasks.initialize()


def load_default_cache_exp(_configs: dict, /) -> None:
    if default_cache_exp := _configs.get('DEFAULT_CACHE_EXP'):
        config.DEFAULT_CACHE_EXP = default_cache_exp


def load_authentication_class(_configs: dict, /) -> None:
    """Should be after `load_secret_key()`"""
    if authentication := _configs.get('AUTHENTICATION'):
        config.AUTHENTICATION = import_class(authentication)

    if ws_authentication := _configs.get('WS_AUTHENTICATION'):
        config.WS_AUTHENTICATION = import_class(ws_authentication)

    load_jwt_config(_configs)


def load_jwt_config(_configs: dict, /) -> None:
    """Only Collect JWT Config If Authentication Is JWTAuthentication"""
    auth_is_jwt = (
            getattr(config.AUTHENTICATION, '__name__', None) == 'JWTAuthentication' or
            getattr(config.WS_AUTHENTICATION, '__name__', None) == 'QueryParamJWTAuthentication'
    )
    jwt = _configs.get('JWTConfig', {})
    if auth_is_jwt or jwt:
        if 'key' not in jwt:
            if config.SECRET_KEY is None:
                raise _exception_handler(field='JWTConfig', error='`JWTConfig.key` or `SECRET_KEY` is required.')
            jwt['key'] = config.SECRET_KEY.decode()
        config.JWT_CONFIG = JWTConfig(**jwt)


def load_urls(_configs: dict, /, urls: dict | None) -> None:
    """
    Return tuple of all urls (as a flat dict) and (as a nested dict)
    """
    if isinstance(urls, dict):
        pass

    elif (url_routing := _configs.get('URLs')) is None:
        raise _exception_handler(field='URLs', error='required.')

    elif isinstance(url_routing, dict):
        error = (
            "can't be 'dict', you may want to pass it's value directly to Panther(). " 'Example: Panther(..., urls=...)'
        )
        raise _exception_handler(field='URLs', error=error)

    elif not isinstance(url_routing, str):
        error = 'should be dotted string.'
        raise _exception_handler(field='URLs', error=error)

    else:
        try:
            urls = import_class(url_routing)
        except ModuleNotFoundError as e:
            raise _exception_handler(field='URLs', error=e)

        if not isinstance(urls, dict):
            raise _exception_handler(field='URLs', error='should point to a dict.')

    config.FLAT_URLS = flatten_urls(urls)
    config.URLS = finalize_urls(config.FLAT_URLS)
    config.URLS['_panel'] = finalize_urls(flatten_urls(panel_urls))


def load_websocket_connections():
    """Should be after `load_redis()`"""
    if config.HAS_WS:
        # Check `websockets`
        try:
            import websockets
        except ImportError as e:
            raise import_error(e, package='websockets')

        # Use the redis pubsub if `redis.is_connected`, else use the `multiprocessing.Manager`
        pubsub_connection = redis.create_connection_for_websocket() if redis.is_connected else Manager()
        config.WEBSOCKET_CONNECTIONS = WebsocketConnections(pubsub_connection=pubsub_connection)


def check_endpoints_inheritance():
    """Should be after `load_urls()`"""
    for _, endpoint in config.FLAT_URLS.items():
        if isinstance(endpoint, types.FunctionType):
            check_function_type_endpoint(endpoint=endpoint)
        else:
            check_class_type_endpoint(endpoint=endpoint)


def _exception_handler(field: str, error: str | Exception) -> PantherError:
    return PantherError(f"Invalid '{field}': {error}")
