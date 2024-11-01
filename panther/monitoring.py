import logging
from time import perf_counter
from typing import Literal

from panther.base_request import BaseRequest
from panther.configs import config

logger = logging.getLogger('monitoring')


class Monitoring:
    """
    Create Log Message Like Below:
    date_time | method | path | ip:port | response_time(seconds) | status
    """
    def __init__(self, is_ws: bool = False):
        self.is_ws = is_ws

    async def before(self, request: BaseRequest):
        if config.MONITORING:
            ip, port = request.client

            if self.is_ws:
                method = 'WS'
            else:
                method = request.scope['method']

            self.log = f'{method} | {request.path} | {ip}:{port}'
            self.start_time = perf_counter()

    async def after(self, status: int | Literal['Accepted', 'Rejected', 'Closed'], /):
        if config.MONITORING:
            response_time = perf_counter() - self.start_time  # Seconds
            logger.info(f'{self.log} | {response_time} | {status}')
