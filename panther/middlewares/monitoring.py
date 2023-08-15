from time import perf_counter

from panther.logger import monitoring_logger
from panther.middlewares.base import BaseMiddleware
from panther.request import Request


class Middleware(BaseMiddleware):
    """
    Create Log Message Like Below:
    [method] path | ip:port | response_time ms | status_code
    """

    async def before(self, request: Request) -> Request:
        ip, port = request.client
        self.log = f'{request.method} | {request.path} | {ip}:{port}'
        self.start_time = perf_counter()
        return request

    async def after(self, status_code: int):
        """
        We handled Monitoring Middle manually,
        cause of that we only have "status_code" here
        """
        response_time = (perf_counter() - self.start_time) * 1_000
        monitoring_logger.info(f'{self.log} | {response_time: .3} ms | {status_code}')
