from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import orjson as json
from panther import status

from panther._utils import generate_ws_connection_id
from panther.base_request import BaseRequest
from panther.configs import config
from panther.logger import logger
from panther.utils import Singleton

if TYPE_CHECKING:
    from redis import Redis


class WebsocketConnections(Singleton):
    def __init__(self):
        self.connections = dict()
        self.connections_count = 0

    def __call__(self, r: Redis | None):
        if r:
            subscriber = r.pubsub()
            subscriber.subscribe('websocket_connections')
            logger.debug("Subscribing: 'websocket_connections'")
            for channel_data in subscriber.listen():
                logger.debug(f'{channel_data=}')
                # Check Type of PubSub Message
                match channel_data['type']:
                    case 'subscribe':
                        continue

                    case 'message':
                        loaded_data = json.loads(channel_data['data'].decode())
                        if (
                                isinstance(loaded_data, dict)
                                and 'connection_id' in loaded_data
                                and (data := loaded_data.get('data'))
                                and (action := loaded_data.get('action'))
                                and (connection := self.connections.get(connection_id := loaded_data['connection_id']))
                       ):
                            # Check Action of WS
                            match action:
                                case 'send':
                                    logger.debug(f'Sending Message to {connection_id}')
                                    asyncio.run(connection.send(data=data))
                                case 'close':
                                    try:
                                        asyncio.run(connection.close(code=data['code'], reason=data['reason']))
                                    except RuntimeError:
                                        # We are trying to disconnect the connection between a thread and a user
                                        # from another thread
                                        # it's working, but we have to find another solution for close the connection
                                        # Error:
                                        # Task <Task pending coro=<Websocket.close()>> got Future
                                        # <Task pending coro=<WebSocketCommonProtocol.transfer_data()>>
                                        # attached to a different loop
                                        pass
                                case _:
                                    logger.debug(f'Unknown Message Action: {action}')
                    case _:
                        logger.debug(f'Unknown Channel Type: {channel_data["type"]}')

    async def new_connection(self, connection: Websocket):
        await connection.connect(**connection.path_variables)
        if connection.is_connected:
            self.connections_count += 1

            # Save New ConnectionID
            self.connections[connection.connection_id] = connection

    def remove_connection(self, connection: Websocket):
        self.connections_count -= 1
        del self.connections[connection.connection_id]


class Websocket(BaseRequest):
    is_connected: bool = False

    async def connect(self, **kwargs):
        """
        Check your conditions then self.accept() the connection
        """
        await self.accept()

    async def accept(self, subprotocol: str = None, headers: dict = None):
        await self.asgi_send({'type': 'websocket.accept', 'subprotocol': subprotocol, 'headers': headers or {}})
        self.is_connected = True

        # Generate ConnectionID
        connection_id = generate_ws_connection_id()
        while connection_id in config['websocket_connections'].connections:
            connection_id = generate_ws_connection_id()

        # Set ConnectionID
        self.set_connection_id(connection_id)

    async def receive(self, data: str | bytes):
        pass

    async def send(self, data: any = None):
        if data:
            if isinstance(data, bytes):
                await self.send_bytes(bytes_data=data)
            elif isinstance(data, str):
                await self.send_text(text_data=data)
            else:
                await self.send_text(text_data=json.dumps(data).decode())

    async def send_text(self, text_data: str):
        await self.asgi_send({'type': 'websocket.send', 'text': text_data})

    async def send_bytes(self, bytes_data: bytes):
        await self.asgi_send({'type': 'websocket.send', 'bytes': bytes_data})

    async def close(self, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = ''):
        self.is_connected = False
        config['websocket_connections'].remove_connection(self)
        await self.asgi_send({'type': 'websocket.close', 'code': code, 'reason': reason})

    async def listen(self):
        while self.is_connected:
            response = await self.asgi_receive()
            if response['type'] == 'websocket.connect':
                continue

            if response['type'] == 'websocket.disconnect':
                break

            if 'text' in response:
                await self.receive(data=response['text'])
            else:
                await self.receive(data=response['bytes'])

    def set_path_variables(self, path_variables: dict):
        self._path_variables = path_variables

    @property
    def path_variables(self):
        return getattr(self, '_path_variables', {})

    def set_connection_id(self, connection_id):
        self._connection_id = connection_id

    @property
    def connection_id(self) -> str:
        connection_id = getattr(self, '_connection_id', None)
        if connection_id is None:
            logger.error('You should first `self.accept()` the connection then use the `self.connection_id`')
        return connection_id

