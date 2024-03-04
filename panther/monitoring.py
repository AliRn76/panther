import logging
from time import perf_counter
from typing import Literal

from panther.base_request import BaseRequest
from panther.configs import config

logger = logging.getLogger('monitoring')


class Monitoring:
    """
    Create Log Message Like Below:
    date time | method | path | ip:port | response_time [ms, s] | status
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
            response_time = perf_counter() - self.start_time
            time_unit = ' s'

            if response_time < 0.01:
                response_time = response_time * 1_000
                time_unit = 'ms'

            elif response_time >= 10:
                response_time = response_time / 60
                time_unit = ' m'

            logger.info(f'{self.log} | {round(response_time, 4)} {time_unit} | {status}')
