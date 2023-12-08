import logging
from time import perf_counter

from panther.request import Request


logger = logging.getLogger('monitoring')


class Monitoring:
    """
    Create Log Message Like Below:
    [method] path | ip:port | response_time ms | status_code
    """
    def __init__(self, is_active: bool):
        self.is_active = is_active

    async def before(self, request: Request):
        if self.is_active:
            ip, port = request.client
            self.log = f'{request.method} | {request.path} | {ip}:{port}'
            self.start_time = perf_counter()

    async def after(self, status_code: int):
        if self.is_active:
            response_time = (perf_counter() - self.start_time) * 1_000
            logger.info(f'{self.log} | {response_time: .3} ms | {status_code}')
