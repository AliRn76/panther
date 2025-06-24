import asyncio
import logging

from panther._utils import is_function_async
from panther.utils import Singleton

logger = logging.getLogger('panther')


class Event(Singleton):
    _startups = []
    _shutdowns = []

    @classmethod
    def startup(cls, func):
        cls._startups.append(func)

        def wrapper():
            return func()

        return wrapper

    @classmethod
    def shutdown(cls, func):
        cls._shutdowns.append(func)

        def wrapper():
            return func()

        return wrapper

    @classmethod
    async def run_startups(cls):
        for func in cls._startups:
            try:
                if is_function_async(func):
                    await func()
                else:
                    func()
            except Exception as e:
                logger.error(f'{func.__name__}() startup event got error: {e}')

    @classmethod
    def run_shutdowns(cls):
        for func in cls._shutdowns:
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

    @classmethod
    def clear(cls):
        """Clear all stored events (useful for testing)"""
        cls._startups.clear()
        cls._shutdowns.clear()
