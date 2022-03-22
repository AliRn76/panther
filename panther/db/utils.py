from panther.logger import logger


def query_logger(func):
    def log(*args, **kwargs):
        # TODO: Time Log
        # logger.info(f'\033[1mQuery -->\033[0m {func.__name__}')
        logger.info(f'Query --> {func.__name__}')
        return func(*args, **kwargs)
    return log

