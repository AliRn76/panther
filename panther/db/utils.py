from panther.logger import logger
from time import perf_counter


def query_logger(func):
    def log(*args, **kwargs):
        # TODO: Log Only If Debug Is True
        Debug = False
        if Debug is False:
            return func(*args, **kwargs)
        start = perf_counter()
        response = func(*args, **kwargs)
        end = perf_counter()
        # logger.info(f'\033[1mQuery -->\033[0m  {args[0].__name__}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        logger.info(f'Query --> {args[0].__name__}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log

