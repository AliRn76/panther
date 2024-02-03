from __future__ import annotations

import asyncio
import contextlib
import logging
from multiprocessing import Manager
from typing import TYPE_CHECKING, Literal

import orjson as json

from panther import status
from panther._utils import generate_ws_connection_id
from panther.base_request import BaseRequest
from panther.configs import config
from panther.db.connection import redis
from panther.utils import Singleton

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger('panther')


class PubSub:
    def __init__(self, manager):
        self._manager = manager
        self._subscribers = self._manager.list()

    def subscribe(self):
        queue = self._manager.Queue()
        self._subscribers.append(queue)
        return queue

    def publish(self, msg):
        for queue in self._subscribers:
            queue.put(msg)


class WebsocketConnections(Singleton):
    def __init__(self, manager: Manager = None):
        self.connections = {}
        self.connections_count = 0
        self.manager = manager

    def __call__(self, r: Redis | None):
        if r:
            subscriber = r.pubsub()
            subscriber.subscribe('websocket_connections')
            logger.info("Subscribed to 'websocket_connections' channel")
            for channel_data in subscriber.listen():
                match channel_data['type']:
                    # Subscribed
                    case 'subscribe':
                        continue

                    # Message Received
                    case 'message':
                        loaded_data = json.loads(channel_data['data'].decode())
                        self._handle_received_message(received_message=loaded_data)

                    case unknown_type:
                        logger.debug(f'Unknown Channel Type: {unknown_type}')
        else:
            self.pubsub = PubSub(manager=self.manager)
            queue = self.pubsub.subscribe()
            logger.info("Subscribed to 'websocket_connections' queue")
            while True:
                received_message = queue.get()
                self._handle_received_message(received_message=received_message)

    def _handle_received_message(self, received_message):
        if (
                isinstance(received_message, dict)
                and (connection_id := received_message.get('connection_id'))
                and connection_id in self.connections
                and 'action' in received_message
                and 'data' in received_message
        ):
            # Check Action of WS
            match received_message['action']:
                case 'send':
                    asyncio.run(self.connections[connection_id].send(data=received_message['data']))
                case 'close':
                    with contextlib.suppress(RuntimeError):
                        asyncio.run(self.connections[connection_id].close(
                            code=received_message['data']['code'],
                            reason=received_message['data']['reason']
                        ))
                        # We are trying to disconnect the connection between a thread and a user
                        # from another thread, it's working, but we have to find another solution for it
                        #
                        # Error:
                        # Task <Task pending coro=<Websocket.close()>> got Future
                        # <Task pending coro=<WebSocketCommonProtocol.transfer_data()>>
                        # attached to a different loop
                case unknown_action:
                    logger.debug(f'Unknown Message Action: {unknown_action}')

    def publish(self, connection_id: str, action: Literal['send', 'close'], data: any):
        publish_data = {'connection_id': connection_id, 'action': action, 'data': data}

        if redis.is_connected:
            redis.publish('websocket_connections', json.dumps(publish_data))
        else:
            self.pubsub.publish(publish_data)

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
        logger.debug(f'Sending WS Message to {self.connection_id}')
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
        logger.debug(f'Closing WS Connection {self.connection_id}')
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
