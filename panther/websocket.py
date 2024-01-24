from __future__ import annotations

from typing import Literal

import orjson as json

from panther import status
from panther.base_websocket import Websocket, PUBSUB
from panther.db.connection import redis


class GenericWebsocket(Websocket):
    async def connect(self, **kwargs):
        """
        Check your conditions then `accept()` the connection
        """

    async def receive(self, data: str | bytes):
        """
        Received `data` of connection,
        You may want to use json.loads() on the `data`
        """

    async def send(self, data: any = None):
        """
        We are using this method to send message to the client,
        You may want to override it with your custom scenario. (not recommended)
        """
        return await super().send(data=data)


async def send_message_to_websocket(connection_id: str, data: any):
    _publish_to_websocket(connection_id=connection_id, action='send', data=data)


async def close_websocket_connection(connection_id: str, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = ''):
    data = {'code': code, 'reason': reason}
    _publish_to_websocket(connection_id=connection_id, action='close', data=data)


def _publish_to_websocket(connection_id: str, action: Literal['send', 'close'], data: any):
    publish_data = {'connection_id': connection_id, 'action': action, 'data': data}

    if redis.is_connected:
        redis.publish('websocket_connections', json.dumps(publish_data))
    else:
        PUBSUB.publish(publish_data)
