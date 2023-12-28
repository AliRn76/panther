import ast
import platform
import sys
from datetime import timedelta
from importlib import import_module
from pathlib import Path
from typing import Callable

from pydantic._internal._model_construction import ModelMetaclass

from panther._utils import import_class
from panther.configs import JWTConfig, config
from panther.exceptions import PantherException
from panther.middlewares.base import WebsocketMiddleware, HTTPMiddleware
from panther.routings import finalize_urls, flatten_urls
from panther.throttling import Throttling

__all__ = (
    'load_configs_module',
    'load_secret_key',
    'load_monitoring',
    'load_log_queries',
    'load_background_tasks',
    'load_throttling',
    'load_default_cache_exp',
    'load_middlewares',
    'load_user_model',
    'load_authentication_class',
    'load_jwt_config',
    'load_startup',
    'load_shutdown',
    'load_auto_reformat',
    'collect_all_models',
    'load_urls',
    'load_panel_urls',
)


def load_configs_module(_configs, /) -> dict:
    """Read the config file and put it as dict in self.configs"""
    if _configs:
        _module = sys.modules[_configs]
    else:
        try:
            _module = import_module('core.configs')
        except ModuleNotFoundError:
            raise _exception_handler(field='core/configs.py', error='Not Found')
    return _module.__dict__


def load_secret_key(configs: dict, /) -> bytes | None:
    if secret_key := configs.get('SECRET_KEY'):
        return secret_key.encode()
    return secret_key


def load_monitoring(configs: dict, /) -> bool:
    return configs.get('MONITORING', config['monitoring'])


def load_log_queries(configs: dict, /) -> bool:
    return configs.get('LOG_QUERIES', config['log_queries'])


def load_background_tasks(configs: dict, /) -> bool:
    return configs.get('BACKGROUND_TASKS', config['background_tasks'])


def load_throttling(configs: dict, /) -> Throttling | None:
    return configs.get('THROTTLING', config['throttling'])


def load_default_cache_exp(configs: dict, /) -> timedelta | None:
    return configs.get('DEFAULT_CACHE_EXP', config['default_cache_exp'])


def load_middlewares(configs: dict, /) -> dict:
    """
    Collect The Middlewares & Set db_engine If One Of Middlewares Was For DB
    And Return a dict with two list, http and ws middlewares"""
    from panther.middlewares import BaseMiddleware

    middlewares = {'http': [], 'ws': []}

    for middleware in configs.get('MIDDLEWARES') or []:
        if not isinstance(middleware, list | tuple):
            raise _exception_handler(field='MIDDLEWARES', error=f'{middleware} should have 2 part: (path, kwargs)')

        if len(middleware) == 1:
            path = middleware[0]
            data = {}

        elif len(middleware) > 2:
            raise _exception_handler(field='MIDDLEWARES', error=f'{middleware} too many arguments')

        else:
            path, data = middleware

        if path.find('panther.middlewares.db.DatabaseMiddleware') != -1:
            config['db_engine'] = data['url'].split(':')[0]
        try:
            Middleware = import_class(path)  # noqa: N806
        except (AttributeError, ModuleNotFoundError):
            raise _exception_handler(field='MIDDLEWARES', error=f'{path} is not a valid middleware path')

        if issubclass(Middleware, BaseMiddleware) is False:
            raise _exception_handler(field='MIDDLEWARES', error='is not a sub class of BaseMiddleware')

        middleware_instance = Middleware(**data)
        if isinstance(middleware_instance, BaseMiddleware | HTTPMiddleware):
            middlewares['http'].append(middleware_instance)
        if isinstance(middleware_instance, BaseMiddleware | WebsocketMiddleware):
            middlewares['ws'].append(middleware_instance)
    return middlewares


def load_user_model(configs: dict, /) -> ModelMetaclass:
    return import_class(configs.get('USER_MODEL', 'panther.db.models.BaseUser'))


def load_authentication_class(configs: dict, /) -> ModelMetaclass | None:
    return configs.get('AUTHENTICATION') and import_class(configs['AUTHENTICATION'])


def load_jwt_config(configs: dict, /) -> JWTConfig | None:
    """Only Collect JWT Config If Authentication Is JWTAuthentication"""
    if getattr(config['authentication'], '__name__', None) == 'JWTAuthentication':
        user_config = configs.get('JWTConfig', {})
        if 'key' not in user_config:
            user_config['key'] = config['secret_key'].decode()

        return JWTConfig(**user_config)
    return None


def load_startup(configs: dict, /) -> Callable:
    return configs.get('STARTUP') and import_class(configs['STARTUP'])


def load_shutdown(configs: dict, /) -> Callable:
    return configs.get('SHUTDOWN') and import_class(configs['SHUTDOWN'])


def load_auto_reformat(configs: dict, /) -> bool:
    return configs.get('AUTO_REFORMAT', config['auto_reformat'])


def collect_all_models() -> list[dict]:
    """Collecting all models for panel APIs"""
    from panther.db.models import Model

    # Just load all the python files from 'base_dir',
    #   so Model.__subclasses__ can find all the subclasses
    slash = '\\' if platform.system() == 'Windows' else '/'
    _parts = '_tail' if sys.version_info >= (3, 12) else '_parts'
    python_files = [
        f for f in config['base_dir'].rglob('*.py')
        if not f.name.startswith('_') and 'site-packages' not in getattr(f.parents, _parts)
    ]
    for file in python_files:
        # Analyse the file
        with Path(file).open() as f:
            node = ast.parse(f.read())

        model_imported = False
        panther_imported = False
        panther_called = False
        for n in node.body:
            match n:

                # from panther.db import Model
                case ast.ImportFrom(module='panther.db', names=[ast.alias(name='Model')]):
                    model_imported = True

                # from panther.db.models import ..., Model, ...
                case ast.ImportFrom(module='panther.db.models', names=[*names]):
                    try:
                        next(v for v in names if v.name == 'Model')
                        model_imported = True
                    except StopIteration:
                        pass

                # from panther import Panther, ...
                case ast.ImportFrom(module='panther', names=[ast.alias(name='Panther'), *_]):
                    panther_imported = True

                # from panther import ..., Panther
                case ast.ImportFrom(module='panther', names=[*_, ast.alias(name='Panther')]):
                    panther_imported = True

                # ... = Panther(...)
                case ast.Assign(value=ast.Call(func=ast.Name(id='Panther'))):
                    panther_called = True

        # Panther() should not be called in the file and Model() should be imported,
        #   We check the import of the Panther to make sure he is calling the panther.Panther and not any Panther
        if panther_imported and panther_called or not model_imported:
            continue

        # Load the module
        dotted_f = str(file).removeprefix(f'{config["base_dir"]}{slash}').removesuffix('.py').replace(slash, '.')
        import_module(dotted_f)

    return [
        {
            'name': m.__name__,
            'module': m.__module__,
            'class': m
        } for m in Model.__subclasses__() if m.__module__ != 'panther.db.models'
    ]


def load_urls(configs: dict, /, urls: dict | None) -> tuple[dict, dict]:
    """
    Return tuple of all urls (as a flat dict) and (as a nested dict)
    """
    if isinstance(urls, dict):
        collected_urls = flatten_urls(urls)
        return collected_urls, finalize_urls(collected_urls)

    if (url_routing := configs.get('URLs')) is None:
        raise _exception_handler(field='URLs', error='is required.')

    if isinstance(url_routing, dict):
        error = (
            "can't be 'dict', you may want to pass it's value directly to Panther(). " 'Example: Panther(..., urls=...)'
        )
        raise _exception_handler(field='URLs', error=error)

    if not isinstance(url_routing, str):
        error = 'should be dotted string.'
        raise _exception_handler(field='URLs', error=error)

    try:
        imported_urls = import_class(url_routing)
    except ModuleNotFoundError as e:
        raise _exception_handler(field='URLs', error=e)

    if not isinstance(imported_urls, dict):
        raise _exception_handler(field='URLs', error='should point to a dict.')

    collected_urls = flatten_urls(imported_urls)
    return collected_urls, finalize_urls(collected_urls)


def load_panel_urls() -> dict:
    from panther.panel.urls import urls

    return finalize_urls(flatten_urls(urls))


def _exception_handler(field: str, error: str | Exception) -> PantherException:
    return PantherException(f"Invalid '{field}': {error}")
