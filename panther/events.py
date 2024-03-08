import asyncio

from panther._utils import is_function_async
from panther.configs import config


class Event:
    @staticmethod
    def startup(func):
        def wrapper():
            config.STARTUPS.append(func)
        return wrapper

    @staticmethod
    def shutdown(func):
        def wrapper():
            config.SHUTDOWNS.append(func)
        return wrapper

    @staticmethod
    async def run_startups():
        for func in config.STARTUPS:
            if is_function_async(func):
                await func()
            else:
                func()

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
