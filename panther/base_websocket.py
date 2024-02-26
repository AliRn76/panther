from __future__ import annotations

import asyncio
import contextlib
import logging
from multiprocessing import Manager
from multiprocessing.managers import SyncManager
from threading import Thread
from typing import TYPE_CHECKING, Literal

import orjson as json

from panther import status
from panther.base_request import BaseRequest
from panther.configs import config
from panther.db.connections import redis
from panther.exceptions import AuthenticationAPIError, InvalidPathVariableAPIError
from panther.utils import Singleton, ULID

if TYPE_CHECKING:
    from redis.asyncio import Redis

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
    def __init__(self, pubsub_connection: Redis | Manager):
        self.connections = {}
        self.connections_count = 0
        self.pubsub_connection = pubsub_connection

        if isinstance(self.pubsub_connection, SyncManager):
            self.pubsub = PubSub(manager=self.pubsub_connection)

    async def __call__(self):
        if isinstance(self.pubsub_connection, SyncManager):
            # We don't have redis connection, so use the `multiprocessing.PubSub`
            queue = self.pubsub.subscribe()
            logger.info("Subscribed to 'websocket_connections' queue")
            while True:
                received_message = queue.get()
                await self._handle_received_message(received_message=received_message)
        else:
            # We have a redis connection, so use it for pubsub
            self.pubsub = self.pubsub_connection.pubsub()
            await self.pubsub.subscribe('websocket_connections')
            logger.info("Subscribed to 'websocket_connections' channel")
            async for channel_data in self.pubsub.listen():
                match channel_data['type']:
                    # Subscribed
                    case 'subscribe':
                        continue

                    # Message Received
                    case 'message':
                        loaded_data = json.loads(channel_data['data'].decode())
                        await self._handle_received_message(received_message=loaded_data)

                    case unknown_type:
                        logger.debug(f'Unknown Channel Type: {unknown_type}')

    async def _handle_received_message(self, received_message):
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
                    await self.connections[connection_id].send(data=received_message['data'])
                case 'close':
                    await self.connections[connection_id].close(
                        code=received_message['data']['code'],
                        reason=received_message['data']['reason']
                    )
                case unknown_action:
                    logger.debug(f'Unknown Message Action: {unknown_action}')

    async def publish(self, connection_id: str, action: Literal['send', 'close'], data: any):
        publish_data = {'connection_id': connection_id, 'action': action, 'data': data}

        if redis.is_connected:
            await redis.publish('websocket_connections', json.dumps(publish_data))
        else:
            self.pubsub.publish(publish_data)

    async def new_connection(self, connection: Websocket) -> None:
        # 1. Authentication
        connection_closed = await self.handle_authentication(connection=connection)

        # 2. Permissions
        connection_closed = connection_closed or await self.handle_permissions(connection=connection)

        if connection_closed:
            # Don't run the following code...
            return None

        # 3. Put PathVariables and Request(If User Wants It) In kwargs
        try:
            kwargs = connection.clean_parameters(connection.connect)
        except InvalidPathVariableAPIError as e:
            return await connection.close(status.WS_1000_NORMAL_CLOSURE, reason=str(e))

        # 4. Connect To Endpoint
        await connection.connect(**kwargs)

        if not hasattr(connection, '_connection_id'):
            # User didn't even call the `self.accept()` so close the connection
            await connection.close()

        # 5. Connection Accepted
        if connection.is_connected:
            self.connections_count += 1

            # Save New ConnectionID
            self.connections[connection.connection_id] = connection

    def remove_connection(self, connection: Websocket) -> None:
        if connection.is_connected:
            self.connections_count -= 1
            del self.connections[connection.connection_id]

    @classmethod
    async def handle_authentication(cls, connection: Websocket) -> bool:
        """Return True if connection is closed, False otherwise."""
        if connection.auth:
            if not config.WS_AUTHENTICATION:
                logger.critical('"WS_AUTHENTICATION" has not been set in configs')
                await connection.close(reason='Authentication Error')
                return True
            try:
                connection.user = await config.WS_AUTHENTICATION.authentication(connection)
            except AuthenticationAPIError as e:
                await connection.close(reason=e.detail)
        return False

    @classmethod
    async def handle_permissions(cls, connection: Websocket) -> bool:
        """Return True if connection is closed, False otherwise."""
        for perm in connection.permissions:
            if type(perm.authorization).__name__ != 'method':
                logger.error(f'{perm.__name__}.authorization should be "classmethod"')
                await connection.close(reason='Permission Denied')
                return True
            if await perm.authorization(connection) is False:
                await connection.close(reason='Permission Denied')
                return True
        return False


class Websocket(BaseRequest):
    is_connected: bool = False
    auth: bool = False
    permissions: list = []

    def __init_subclass__(cls, **kwargs):
        if cls.__module__ != 'panther.websocket':
            config.HAS_WS = True

    async def connect(self, **kwargs) -> None:
        pass

    async def receive(self, data: str | bytes) -> None:
        pass

    async def accept(self, subprotocol: str | None = None, headers: dict | None = None) -> None:
        await self.asgi_send({'type': 'websocket.accept', 'subprotocol': subprotocol, 'headers': headers or {}})
        self.is_connected = True

        # Generate ConnectionID
        self._connection_id = ULID.new()

        logger.debug(f'Accepting WS Connection {self._connection_id}')

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
        connection_id = getattr(self, '_connection_id', '')
        logger.debug(f'Closing WS Connection {connection_id} Code: {code}')
        self.is_connected = False
        config.WEBSOCKET_CONNECTIONS.remove_connection(self)
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

    @property
    def connection_id(self) -> str:
        if not hasattr(self, '_connection_id'):
            logger.error('You should first `self.accept()` the connection then use the `self.connection_id`')
        return self._connection_id
