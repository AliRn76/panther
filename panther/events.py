import asyncio
import logging

from panther._utils import is_function_async
from panther.configs import config

logger = logging.getLogger('panther')


class Event:
    @staticmethod
    def startup(func):
        config.STARTUPS.append(func)

        def wrapper():
            return func()
        return wrapper

    @staticmethod
    def shutdown(func):
        config.SHUTDOWNS.append(func)

        def wrapper():
            return func()
        return wrapper

    @staticmethod
    async def run_startups():
        for func in config.STARTUPS:
            try:
                if is_function_async(func):
                    await func()
                else:
                    func()
            except Exception as e:
                logger.error(f'{func.__name__}() startup event got error: {e}')

    @staticmethod
    def run_shutdowns():
        for func in config.SHUTDOWNS:
            if is_function_async(func):
                try:
                    asyncio.run(func())
                except ModuleNotFoundError:
                    # Error: import of asyncio halted; None in sys.modules
                    #   And as I figured it out, it only happens when we are running with
                    #   gunicorn and Uvicorn workers (-k uvicorn.workers.UvicornWorker)
                    pass
            else:
                func()
