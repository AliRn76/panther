import logging
from time import perf_counter

from panther.base_websocket import Websocket
from panther.middlewares import HTTPMiddleware, WebsocketMiddleware
from panther.request import Request

logger = logging.getLogger('monitoring')


class MonitoringMiddleware(HTTPMiddleware):
    """
    Create Log Message Like Below:
    datetime | method | path | ip:port | response_time(seconds) | status
    """

    async def __call__(self, request: Request):
        start_time = perf_counter()
        method = request.scope['method']

        response = await self.dispatch(request=request)

        response_time = perf_counter() - start_time  # Seconds
        logger.info(f'{method} | {request.path} | {request.client} | {response_time} | {response.status_code}')
        return response


class WebsocketMonitoringMiddleware(WebsocketMiddleware):
    """
    Create Log Message Like Below:
    datetime | WS | path | ip:port | connection_time(seconds) | status
    """

    ConnectedConnectionTime = ' - '

    async def __call__(self, connection: Websocket):
        start_time = perf_counter()

        logger.info(f'WS | {connection.path} | {connection.client} |{self.ConnectedConnectionTime}| {connection.state}')
        connection = await self.dispatch(connection=connection)

        connection_time = perf_counter() - start_time  # Seconds
        logger.info(f'WS | {connection.path} | {connection.client} | {connection_time} | {connection.state}')
        return connection
