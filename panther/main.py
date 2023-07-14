import os
import ast
import sys
import asyncio
from pathlib import Path
from runpy import run_path
from pydantic._internal._model_construction import ModelMetaclass

from panther import status
from panther.request import Request
from panther.response import Response
from panther.exceptions import APIException
from panther.configs import JWTConfig, config
from panther.middlewares.base import BaseMiddleware
from panther.middlewares.monitoring import Middleware as MonitoringMiddleware
from panther.routings import find_endpoint, check_and_load_urls, finalize_urls, flatten_urls, collect_path_variables
from panther._utils import http_response, import_class, read_body

""" We can't import logger on the top cause it needs config['base_dir'] ans its fill in __init__ """


class Panther:

    def __init__(self, name):
        from panther.logger import logger
        os.system('clear')
        config['base_dir'] = Path(name).resolve().parent
        self.panther_dir = Path(__file__).parent
        if sys.version_info.minor < 11:
            logger.warning('Use Python Version 3.11+ For Better Performance.')
        self.load_configs()

    def load_configs(self) -> None:
        from panther.logger import logger
        logger.debug(f'Base directory: {config["base_dir"]}')

        # Check & Read The Configs File
        self._check_configs()

        # Put Variables In "config"
        config['monitoring'] = self.settings.get('MONITORING', config['monitoring'])
        config['log_queries'] = self.settings.get('LOG_QUERIES', config['log_queries'])
        config['default_cache_exp'] = self.settings.get('DEFAULT_CACHE_EXP', config['default_cache_exp'])
        config['throttling'] = self.settings.get('THROTTLING', config['throttling'])
        config['secret_key'] = self._get_secret_key()

        config['middlewares'] = self._get_middlewares()
        config['reversed_middlewares'] = config['middlewares'][::-1]
        config['user_model'] = self._get_user_model()

        config['authentication'] = self._get_authentication_class()
        config['jwt_config'] = self._get_jwt_config()

        # Find Database Models
        self._collect_models()

        # Check & Collect URLs
        #   check_urls should be the last call in load_configs,
        #   because it will read all files and load them.
        config['urls'] = self._load_urls()

        # This import shouldn't be on top
        from panther.panel.urls import urls as panel_urls
        config['urls']['_panel'] = panel_urls

        logger.debug('Configs loaded.')
        if config['monitoring']:
            logger.info('Run "panther monitor" in another session for Monitoring.')

    def _check_configs(self):
        from panther.logger import logger
        """Read the config file and put it as dict in self.settings"""
        try:
            configs_path = config['base_dir'] / 'core/configs.py'
            self.settings = run_path(str(configs_path))
        except FileNotFoundError:
            logger.critical('core/configs.py Not Found.')
            # TODO: Exit() Here

    def _get_secret_key(self) -> bytes | None:
        if secret_key := self.settings.get('SECRET_KEY'):
            return secret_key.encode()
        return secret_key

    def _get_middlewares(self) -> list:
        """Collect The Middlewares & Set db_engine If One Of Middlewares Was For DB"""
        from panther.logger import logger
        middlewares = list()

        for path, data in self.settings.get('MIDDLEWARES', []):
            if path.find('panther.middlewares.db.Middleware') != -1:
                config['db_engine'] = data['url'].split(':')[0]

            Middleware = import_class(path)  # NOQA: Py Pep8 Naming
            if not issubclass(Middleware, BaseMiddleware):
                logger.critical(f'{Middleware} is not a sub class of BaseMiddleware.')
                continue

            middlewares.append(Middleware(**data))  # NOQA: Py Argument List
        return middlewares

    def _get_user_model(self) -> ModelMetaclass:
        return import_class(self.settings.get('USER_MODEL', 'panther.db.models.BaseUser'))

    def _get_authentication_class(self) -> ModelMetaclass | None:
        return self.settings.get('AUTHENTICATION') and import_class(self.settings['AUTHENTICATION'])

    def _get_jwt_config(self) -> JWTConfig:
        """Only Collect JWT Config If Authentication Is JWTAuthentication"""
        if getattr(config['authentication'], '__name__', None) == 'JWTAuthentication':
            user_config = self.settings.get('JWTConfig')
            return JWTConfig(**user_config) if user_config else JWTConfig(key=config['secret_key'].decode())

    @classmethod
    def _collect_models(cls):
        """Collecting models for panel APIs"""
        from panther.db.models import Model

        for root, _, files in os.walk(config['base_dir']):
            # Traverse through each directory
            for f in files:
                # Traverse through each file of directory
                if f == 'models.py':
                    # If the file was "models.py" read it
                    file_path = f'{root}/models.py'
                    with open(file_path, 'r') as file:
                        # Parse the file with ast
                        node = ast.parse(file.read())
                        for n in node.body:
                            # Find classes in each element of files' body
                            if type(n) is ast.ClassDef and n.bases:
                                class_path = file_path\
                                    .removesuffix('/models.py')\
                                    .removeprefix(f'{config["base_dir"]}/')\
                                    .replace('/', '.')
                                # We don't need to import the package classes
                                if class_path.find('site-packages') == -1:
                                    # Import the class to check his father and brother
                                    klass = import_class(f'{class_path}.models.{n.name}')
                                    for parent in klass.__mro__:
                                        if parent is Model:
                                            # The class was one our database models so collect it
                                            config['models'].append({
                                                'name': n.name,
                                                'path':  file_path,
                                                'class': klass,
                                                'app': class_path.split('.'),
                                            })

    def _load_urls(self) -> dict:
        urls = check_and_load_urls(self.settings.get('URLs')) or {}
        collected_urls = flatten_urls(urls)
        return finalize_urls(collected_urls)

    async def __call__(self, scope, receive, send) -> None:
        """
        We Used Python3.11+ For asyncio.TaskGroup()
        1.
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.run(scope, receive, send))
        2.
            await self.run(scope, receive, send)
        3.
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(self.run, scope, receive, send)
                await anyio.to_thread.run_sync(self.run, scope, receive, send)
        4.
            with ProcessPoolExecutor() as e:
                e.submit(self.run, scope, receive, send)
        """
        if sys.version_info.minor >= 11:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.run(scope, receive, send))
        else:
            await self.run(scope, receive, send)

    async def run(self, scope, receive, send):
        from panther.logger import logger
        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)

        # Monitoring Middleware
        monitoring_middleware = None
        if config['monitoring']:
            monitoring_middleware = MonitoringMiddleware()
            await monitoring_middleware.before(request=request)

        # Find Endpoint
        endpoint, found_path = find_endpoint(path=request.path)
        path_variables = collect_path_variables(request_path=request.path, found_path=found_path)

        if endpoint is None:
            return await http_response(
                send, status_code=status.HTTP_404_NOT_FOUND, monitoring=monitoring_middleware, exception=True,
            )

        try:  # They Both Have The Save Exception (APIException)
            # Call 'Before' Middlewares
            for middleware in config['middlewares']:
                request = await middleware.before(request=request)

            # User Didn't Use @API Decorator
            if not hasattr(endpoint, '__wrapped__'):
                logger.critical(f'You may have forgotten to use @API on the {endpoint.__name__}()')
                return await http_response(
                    send,
                    status_code=status.HTTP_510_NOT_EXTENDED,
                    monitoring=monitoring_middleware,
                    exception=True,
                )

            # Call Endpoint
            response = await endpoint(request=request, **path_variables)
        except APIException as e:
            response = self.handle_exceptions(e)
        except Exception as e:
            # Every unhandled exception in Panther or code will catch here
            logger.critical(e)
            return await http_response(
                send,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                monitoring=monitoring_middleware,
                exception=True,
            )

        # Call 'After' Middleware
        for middleware in config['reversed_middlewares']:
            try:
                response = await middleware.after(response=response)
            except APIException as e:
                response = self.handle_exceptions(e)

        await http_response(
            send, status_code=response.status_code, monitoring=monitoring_middleware, body=response.body,
        )

    @classmethod
    def handle_exceptions(cls, e, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code,
        )
