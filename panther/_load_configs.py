import sys
import logging
import types
from importlib import import_module
from multiprocessing import Manager

from panther._utils import import_class
from panther.base_websocket import Websocket, WebsocketConnections
from panther.configs import JWTConfig, config
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.exceptions import PantherException
from panther.middlewares.base import WebsocketMiddleware, HTTPMiddleware
from panther.panel.urls import urls as panel_urls
from panther.routings import finalize_urls, flatten_urls

__all__ = (
    'load_configs_module',
    'load_startup',
    'load_shutdown',
    'load_database',
    'load_secret_key',
    'load_monitoring',
    'load_throttling',
    'load_user_model',
    'load_log_queries',
    'load_middlewares',
    'load_auto_reformat',
    'load_background_tasks',
    'load_default_cache_exp',
    'load_pantherdb_encryption',
    'load_authentication_class',
    'load_urls',
    'load_websocket_connections',
)

logger = logging.getLogger('panther')


def load_configs_module(_configs, /) -> dict:
    """Read the config file as dict"""
    if _configs:
        _module = sys.modules[_configs]
    else:
        try:
            _module = import_module('core.configs')
        except ModuleNotFoundError:
            raise _exception_handler(field='core/configs.py', error='Not Found')
    return _module.__dict__


def load_startup(_configs: dict, /) -> None:
    if startup := _configs.get('STARTUP'):
        startup = import_class(startup)
    config['startup'] = startup


def load_shutdown(_configs: dict, /) -> None:
    if shutdown := _configs.get('SHUTDOWN'):
        shutdown = import_class(shutdown)
    config['shutdown'] = shutdown


def load_database(_configs: dict, /) -> None:
    database_config = _configs.get('DATABASE', {})
    if 'engine' in database_config:
        engine_class_path = database_config['engine']['class']
        engine_class = import_class(engine_class_path)
        args = database_config['engine'].copy()
        args.pop('class')
        config['database'] = engine_class(**args)

        if engine_class_path == 'panther.db.connections.PantherDBConnection':
            config['query_engine'] = BasePantherDBQuery
        elif engine_class_path == 'panther.db.connections.MongoDBConnection':
            config['query_engine'] = BaseMongoDBQuery

    if 'query' in database_config:
        if config['query_engine']:
            logger.warning('`DATABASE.query` has already been filled.')
        config['query_engine'] = import_class(database_config['query'])


def load_secret_key(_configs: dict, /) -> None:
    if secret_key := _configs.get('SECRET_KEY'):
        secret_key = secret_key.encode()
    config['secret_key'] = secret_key


def load_monitoring(_configs: dict, /) -> None:
    if monitoring := _configs.get('MONITORING'):
        config['monitoring'] = monitoring


def load_throttling(_configs: dict, /) -> None:
    if throttling := _configs.get('THROTTLING'):
        config['throttling'] = throttling


def load_user_model(_configs: dict, /) -> None:
    config['user_model'] = import_class(_configs.get('USER_MODEL', 'panther.db.models.BaseUser'))
    config['models'].append(config['user_model'])


def load_log_queries(_configs: dict, /) -> None:
    if log_queries := _configs.get('LOG_QUERIES'):
        config['log_queries'] = log_queries


def load_middlewares(_configs: dict, /) -> None:
    """
    Should be after `load_database()`

    Collect The Middlewares & Set `DatabaseMiddleware` If it is needed.
    """
    from panther.middlewares import BaseMiddleware

    middlewares = {'http': [], 'ws': []}

    # Add Database Middleware
    if config['database']:
        database_middleware = import_class('panther.middlewares.db.DatabaseMiddleware')
        middlewares['http'].append(database_middleware())
        middlewares['ws'].append(database_middleware())

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

        middleware_instance = middleware_class(**data)
        if isinstance(middleware_instance, BaseMiddleware | HTTPMiddleware):
            middlewares['http'].append(middleware_instance)

        if isinstance(middleware_instance, BaseMiddleware | WebsocketMiddleware):
            middlewares['ws'].append(middleware_instance)

    config['http_middlewares'] = middlewares['http']
    config['ws_middlewares'] = middlewares['ws']
    config['reversed_http_middlewares'] = middlewares['http'][::-1]
    config['reversed_ws_middlewares'] = middlewares['ws'][::-1]


def load_auto_reformat(_configs: dict, /) -> None:
    if auto_reformat := _configs.get('AUTO_REFORMAT'):
        config['auto_reformat'] = auto_reformat


def load_background_tasks(_configs: dict, /) -> None:
    if background_tasks := _configs.get('BACKGROUND_TASKS'):
        config['background_tasks'] = background_tasks
        config['background_tasks'].initialize()


def load_default_cache_exp(_configs: dict, /) -> None:
    if default_cache_exp := _configs.get('DEFAULT_CACHE_EXP'):
        config['default_cache_exp'] = default_cache_exp


def load_pantherdb_encryption(_configs: dict, /) -> None:
    if pantherdb_encryption := _configs.get('PANTHERDB_ENCRYPTION'):
        config['pantherdb_encryption'] = pantherdb_encryption


def load_authentication_class(_configs: dict, /) -> None:
    """Should be after `load_secret_key()`"""
    if authentication := _configs.get('AUTHENTICATION'):
        authentication = import_class(authentication)
    if ws_authentication := _configs.get('WS_AUTHENTICATION'):
        ws_authentication = import_class(ws_authentication)
    config['authentication'] = authentication
    config['ws_authentication'] = ws_authentication
    load_jwt_config(_configs)


def load_jwt_config(_configs: dict, /) -> None:
    """Only Collect JWT Config If Authentication Is JWTAuthentication"""
    auth_is_jwt = (
            getattr(config['authentication'], '__name__', None) == 'JWTAuthentication' or
            getattr(config['ws_authentication'], '__name__', None) == 'QueryParamJWTAuthentication'
    )
    jwt = _configs.get('JWTConfig', {})
    if auth_is_jwt or jwt:
        if 'key' not in jwt:
            if config['secret_key'] is None:
                raise _exception_handler(field='JWTConfig', error='`JWTConfig.key` or `SECRET_KEY` is required.')
            jwt['key'] = config['secret_key'].decode()
        config['jwt_config'] = JWTConfig(**jwt)


def load_urls(_configs: dict, /, urls: dict | None) -> None:
    """
    Return tuple of all urls (as a flat dict) and (as a nested dict)
    """
    if isinstance(urls, dict):
        pass

    elif (url_routing := _configs.get('URLs')) is None:
        raise _exception_handler(field='URLs', error='is required.')

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

    config['flat_urls'] = flatten_urls(urls)
    config['urls'] = finalize_urls(config['flat_urls'])
    config['urls']['_panel'] = finalize_urls(flatten_urls(panel_urls))


def load_has_ws() -> None:
    """Should be after `load_urls()`"""
    for endpoint in config['flat_urls'].values():
        if not isinstance(endpoint, types.FunctionType) and issubclass(endpoint, Websocket):
            config['has_ws'] = True
            break
    else:
        config['has_ws'] = False


def load_websocket_connections():
    """Should be after `load_urls() & load_middlewares()`"""
    load_has_ws()

    # Create websocket connections instance
    if config['has_ws']:
        # Websocket Redis Connection
        for middleware in config['http_middlewares']:
            if middleware.__class__.__name__ == 'RedisMiddleware':
                redis_connection = middleware.redis_connection_for_ws()
                break
        else:
            redis_connection = None

        # Don't create Manager() if we are going to use Redis for PubSub
        manager = None if redis_connection else Manager()
        config['websocket_connections'] = WebsocketConnections(manager=manager, redis_connection=redis_connection)


def _exception_handler(field: str, error: str | Exception) -> PantherException:
    return PantherException(f"Invalid '{field}': {error}")
