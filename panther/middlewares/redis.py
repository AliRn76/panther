from redis import Redis

from panther.db.connection import RedisConnection
from panther.logger import logger
from panther.middlewares.base import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class RedisMiddleware(BaseMiddleware):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.validate_host()
        self.validate_port()

    def validate_host(self):
        if host := self.kwargs.get('host'):  # noqa: F841
            if False:  # TODO: should be valid ip or domain (then remove the 'noqa')
                logger.critical('Redis "host" is not valid.')
        else:
            self.kwargs['host'] = '127.0.0.1'

    def validate_port(self):
        port = self.kwargs.setdefault('port', 6379)
        if not isinstance(port, int):
            logger.critical('Redis "port" is not valid.')

    async def before(self, request: Request | GenericWebsocket) -> Request | GenericWebsocket:
        self.redis = RedisConnection(**self.kwargs)
        return request

    async def after(self, response: Response | GenericWebsocket) -> Response | GenericWebsocket:
        self.redis.close()
        return response

    def redis_connection_for_ws(self) -> Redis:
        return Redis(**self.kwargs)
