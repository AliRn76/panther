from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

import orjson as json

from panther import status
from panther._utils import generate_ws_connection_id
from panther.base_request import BaseRequest
from panther.configs import config
from panther.utils import Singleton

if TYPE_CHECKING:
    from redis import Redis


logger = logging.getLogger('panther')


class WebsocketConnections(Singleton):
    def __init__(self):
        self.connections = {}
        self.connections_count = 0

    def __call__(self, r: Redis | None):
        if r:
            subscriber = r.pubsub()
            subscriber.subscribe('websocket_connections')
            logger.info("Subscribed to 'websocket_connections' channel")
            for channel_data in subscriber.listen():
                # Check Type of PubSub Message
                match channel_data['type']:
                    case 'subscribe':
                        continue

                    case 'message':
                        loaded_data = json.loads(channel_data['data'].decode())
                        if (
                                isinstance(loaded_data, dict)
                                and (connection_id := loaded_data.get('connection_id'))
                                and (data := loaded_data.get('data'))
                                and (action := loaded_data.get('action'))
                                and (connection := self.connections.get(connection_id))
                       ):
                            # Check Action of WS
                            match action:
                                case 'send':
                                    logger.debug(f'Sending Message to {connection_id}')
                                    asyncio.run(connection.send(data=data))
                                case 'close':
                                    with contextlib.suppress(RuntimeError):
                                        asyncio.run(connection.close(code=data['code'], reason=data['reason']))
                                        # We are trying to disconnect the connection between a thread and a user
                                        # from another thread, it's working, but we have to find another solution it
                                        #
                                        # Error:
                                        # Task <Task pending coro=<Websocket.close()>> got Future
                                        # <Task pending coro=<WebSocketCommonProtocol.transfer_data()>>
                                        # attached to a different loop
                                case _:
                                    logger.debug(f'Unknown Message Action: {action}')
                    case _:
                        logger.debug(f'Unknown Channel Type: {channel_data["type"]}')

    async def new_connection(self, connection: Websocket) -> None:
        await connection.connect(**connection.path_variables)
        if not hasattr(connection, '_connection_id'):
            # User didn't even call the `self.accept()` so close the connection
            await connection.close()

        if connection.is_connected:
            self.connections_count += 1

            # Save New ConnectionID
            self.connections[connection.connection_id] = connection

    def remove_connection(self, connection: Websocket) -> None:
        if connection.is_connected:
            self.connections_count -= 1
            del self.connections[connection.connection_id]


class Websocket(BaseRequest):
    is_connected: bool = False

    async def connect(self, **kwargs) -> None:
        """Check your conditions then self.accept() the connection"""
        await self.accept()

    async def accept(self, subprotocol: str | None = None, headers: dict | None = None) -> None:
        await self.asgi_send({'type': 'websocket.accept', 'subprotocol': subprotocol, 'headers': headers or {}})
        self.is_connected = True

        # Generate ConnectionID
        connection_id = generate_ws_connection_id()
        while connection_id in config['websocket_connections'].connections:
            connection_id = generate_ws_connection_id()

        # Set ConnectionID
        self.set_connection_id(connection_id)

    async def receive(self, data: str | bytes) -> None:
        pass

    async def send(self, data: any = None) -> None:
        if data:
            if isinstance(data, bytes):
                await self.send_bytes(bytes_data=data)
            elif isinstance(data, str):
                await self.send_text(text_data=data)
            else:
                await self.send_text(text_data=json.dumps(data).decode())

    async def send_text(self, text_data: str) -> None:
        await self.asgi_send({'type': 'websocket.send', 'text': text_data})

    async def send_bytes(self, bytes_data: bytes) -> None:
        await self.asgi_send({'type': 'websocket.send', 'bytes': bytes_data})

    async def close(self, code: int = status.WS_1000_NORMAL_CLOSURE, reason: str = '') -> None:
        self.is_connected = False
        config['websocket_connections'].remove_connection(self)
        await self.asgi_send({'type': 'websocket.close', 'code': code, 'reason': reason})

    async def listen(self) -> None:
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

    def set_path_variables(self, path_variables: dict) -> None:
        self._path_variables = path_variables

    @property
    def path_variables(self) -> dict:
        return getattr(self, '_path_variables', {})

    def set_connection_id(self, connection_id: str) -> None:
        self._connection_id = connection_id

    @property
    def connection_id(self) -> str:
        connection_id = getattr(self, '_connection_id', None)
        if connection_id is None:
            logger.error('You should first `self.accept()` the connection then use the `self.connection_id`')
        return connection_id
