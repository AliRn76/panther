import logging
import sys
import types
from importlib import import_module
from multiprocessing import Manager

import jinja2

from panther._utils import check_class_type_endpoint, check_function_type_endpoint, import_class
from panther.background_tasks import _background_tasks
from panther.base_websocket import WebsocketConnections
from panther.cli.utils import import_error
from panther.configs import JWTConfig, config
from panther.db.connections import redis
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.exceptions import PantherError
from panther.middlewares.base import HTTPMiddleware, WebsocketMiddleware
from panther.middlewares.monitoring import MonitoringMiddleware, WebsocketMonitoringMiddleware
from panther.panel.views import HomeView
from panther.routings import finalize_urls, flatten_urls

__all__ = (
    'check_endpoints_inheritance',
    'load_authentication_class',
    'load_auto_reformat',
    'load_background_tasks',
    'load_configs_module',
    'load_database',
    'load_log_queries',
    'load_middlewares',
    'load_other_configs',
    'load_redis',
    'load_secret_key',
    'load_templates_dir',
    'load_throttling',
    'load_timezone',
    'load_urls',
    'load_user_model',
    'load_websocket_connections',
)

logger = logging.getLogger('panther')
monitoring_logger = logging.getLogger('monitoring')


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


def load_timezone(_configs: dict, /) -> None:
    if timezone := _configs.get('TIMEZONE'):
        config.TIMEZONE = timezone


def load_templates_dir(_configs: dict, /) -> None:
    if templates_dir := _configs.get('TEMPLATES_DIR', '.'):
        config.TEMPLATES_DIR = templates_dir

    if config.TEMPLATES_DIR == '.':
        config.TEMPLATES_DIR = config.BASE_DIR

    config.JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            loaders=(
                jinja2.FileSystemLoader(searchpath=config.TEMPLATES_DIR),
                jinja2.PackageLoader(package_name='panther', package_path='panel/templates/'),
                jinja2.PackageLoader(package_name='panther', package_path='openapi/templates/'),
            ),
        ),
    )


def load_database(_configs: dict, /) -> None:
    database_config = _configs.get('DATABASE', {})
    if 'engine' in database_config:
        if 'class' not in database_config['engine']:
            raise _exception_handler(field='DATABASE', error='`engine["class"]` not found.')

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
        config.SECRET_KEY = secret_key


def load_throttling(_configs: dict, /) -> None:
    if throttling := _configs.get('THROTTLING'):
        config.THROTTLING = throttling


def load_user_model(_configs: dict, /) -> None:
    config.USER_MODEL = import_class(_configs.get('USER_MODEL', 'panther.db.models.BaseUser'))
    if config.USER_MODEL not in config.MODELS:
        config.MODELS.append(config.USER_MODEL)


def load_log_queries(_configs: dict, /) -> None:
    if _configs.get('LOG_QUERIES'):
        config.LOG_QUERIES = True


def load_middlewares(_configs: dict, /) -> None:
    # Collect HTTP Middlewares
    for middleware in _configs.get('MIDDLEWARES') or []:
        # This block is for Backward Compatibility
        if isinstance(middleware, list | tuple):
            if len(middleware) == 1:
                middleware = middleware[0]
            elif len(middleware) == 2:
                _deprecated_warning(
                    field='MIDDLEWARES',
                    message='`data` does not supported in middlewares anymore, as your data is static you may want '
                    'to pass them to your middleware with config variables',
                )
                middleware = middleware[0]
            else:
                raise _exception_handler(
                    field='MIDDLEWARES',
                    error=f'{middleware} should be dotted path or type of a middleware class',
                )

        # `middleware` can be type or path of a class
        if not callable(middleware):
            try:
                middleware = import_class(middleware)
            except (AttributeError, ModuleNotFoundError):
                raise _exception_handler(
                    field='MIDDLEWARES',
                    error=f'{middleware} is not a valid middleware path or type',
                )

        if not issubclass(middleware, HTTPMiddleware):
            raise _exception_handler(field='MIDDLEWARES', error=f'{middleware} is not a sub class of `HTTPMiddleware`')

        if issubclass(middleware, MonitoringMiddleware):
            monitoring_logger.debug('')  # Initiated
            config.MONITORING = True

        config.HTTP_MIDDLEWARES.append(middleware)

    # Collect WebSocket Middlewares
    for middleware in _configs.get('WS_MIDDLEWARES') or []:
        # `middleware` can be type or path of a class
        if not callable(middleware):
            try:
                middleware = import_class(middleware)
            except (AttributeError, ModuleNotFoundError):
                raise _exception_handler(
                    field='WS_MIDDLEWARES',
                    error=f'{middleware} is not a valid middleware path or type',
                )

        if not issubclass(middleware, WebsocketMiddleware):
            raise _exception_handler(
                field='WS_MIDDLEWARES', error=f'{middleware} is not a sub class of `WebsocketMiddleware`'
            )

        if issubclass(middleware, WebsocketMonitoringMiddleware):
            monitoring_logger.debug('')  # Initiated
            config.MONITORING = True

        config.WS_MIDDLEWARES.append(middleware)


def load_auto_reformat(_configs: dict, /) -> None:
    if _configs.get('AUTO_REFORMAT'):
        config.AUTO_REFORMAT = True


def load_background_tasks(_configs: dict, /) -> None:
    if _configs.get('BACKGROUND_TASKS'):
        config.BACKGROUND_TASKS = True
        _background_tasks.initialize()


def load_other_configs(_configs: dict, /) -> None:
    known_configs = set(config.__dataclass_fields__)
    for key, value in _configs.items():
        if key.isupper() and key not in known_configs:
            config[key] = value


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
            "can't be 'dict', you may want to pass it's value directly to Panther(). Example: Panther(..., urls=...)"
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


def load_authentication_class(_configs: dict, /) -> None:
    """Should be after `load_secret_key()` and `load_urls()`"""
    if authentication := _configs.get('AUTHENTICATION'):
        config.AUTHENTICATION = import_class(authentication)

    if ws_authentication := _configs.get('WS_AUTHENTICATION'):
        config.WS_AUTHENTICATION = import_class(ws_authentication)

    load_jwt_config(_configs)


def load_jwt_config(_configs: dict, /) -> None:
    """Only Collect JWT Config If Authentication Is JWTAuthentication"""
    from panther.authentications import JWTAuthentication

    auth_is_jwt = (config.AUTHENTICATION and issubclass(config.AUTHENTICATION, JWTAuthentication)) or (
        config.WS_AUTHENTICATION and issubclass(config.WS_AUTHENTICATION, JWTAuthentication)
    )
    jwt = _configs.get('JWT_CONFIG', {})
    using_panel_views = HomeView in config.FLAT_URLS.values()
    if auth_is_jwt or using_panel_views:
        if 'key' not in jwt:
            if config.SECRET_KEY is None:
                raise _exception_handler(field='JWTConfig', error='`JWTConfig.key` or `SECRET_KEY` is required.')
            jwt['key'] = config.SECRET_KEY
        config.JWT_CONFIG = JWTConfig(**jwt)


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
    for endpoint in config.FLAT_URLS.values():
        if endpoint == {}:
            continue

        if isinstance(endpoint, types.FunctionType):
            check_function_type_endpoint(endpoint=endpoint)
        else:
            check_class_type_endpoint(endpoint=endpoint)


def _exception_handler(field: str, error: str | Exception) -> PantherError:
    return PantherError(f"Invalid '{field}': {error}")


def _deprecated_warning(field: str, message: str):
    return logger.warning(f"DEPRECATED '{field}': {message}")
