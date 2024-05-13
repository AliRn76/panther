from __future__ import annotations

import asyncio
import orjson as json
from multiprocessing.managers import SyncManager
from typing import TYPE_CHECKING, Literal

import logging
from panther import status
from panther.base_request import BaseRequest
from panther.configs import config
from panther.db.connections import redis
from panther.exceptions import AuthenticationAPIError, InvalidPathVariableAPIError
from panther.monitoring import Monitoring
from panther.utils import Singleton, ULID

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger('panther')


class PubSub:
    def __init__(self, manager: SyncManager):
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
    def __init__(self, pubsub_connection: Redis | SyncManager):
        self.connections = {}
        self.connections_count = 0
        self.pubsub_connection = pubsub_connection

        if isinstance(self.pubsub_connection, SyncManager):
            self.pubsub = PubSub(manager=self.pubsub_connection)

    async def __call__(self):
        if isinstance(self.pubsub_connection, SyncManager):
            # We don't have redis connection, so use the `multiprocessing.Manager`
            self.pubsub: PubSub
            queue = self.pubsub.subscribe()
            logger.info("Subscribed to 'websocket_connections' queue")
            while True:
                try:
                    received_message = await asyncio.to_thread(queue.get)
                    if received_message is None:
                        # The None came from the CancelledError, so break the loop
                        break
                    await self._handle_received_message(received_message=received_message)
                except (InterruptedError, asyncio.CancelledError):
                    # Put the None to the queue, so the executor knows that it ends
                    queue.put(None)
                    break
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
                        logger.error(f'Unknown Channel Type: {unknown_type}')

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
                    logger.error(f'Unknown Message Action: {unknown_action}')

    async def publish(self, connection_id: str, action: Literal['send', 'close'], data: any):
        publish_data = {'connection_id': connection_id, 'action': action, 'data': data}

        if redis.is_connected:
            await redis.publish('websocket_connections', json.dumps(publish_data))
        else:
            self.pubsub.publish(publish_data)

    async def listen(self, connection: Websocket) -> None:
        # 1. Authentication
        if not connection.is_rejected:
            await self.handle_authentication(connection=connection)

        # 2. Permissions
        if not connection.is_rejected:
            await self.handle_permissions(connection=connection)

        if connection.is_rejected:
            # Connection is rejected so don't continue the flow ...
            return None

        # 3. Put PathVariables and Request(If User Wants It) In kwargs
        try:
            kwargs = connection.clean_parameters(connection.connect)
        except InvalidPathVariableAPIError as e:
            connection.log(e.detail)
            return await connection.close()

        # 4. Connect To Endpoint
        await connection.connect(**kwargs)

        # 5. Check Connection
        if not connection.is_connected and not connection.is_rejected:
            # User didn't call the `self.accept()` or `self.close()` so we `close()` the connection (reject)
            return await connection.close()

        # 6. Listen Connection
        await self.listen_connection(connection=connection)

    async def listen_connection(self, connection: Websocket):
        while True:
            response = await connection.asgi_receive()
            if response['type'] == 'websocket.connect':
                continue

            if response['type'] == 'websocket.disconnect':
                # Connect has to be closed by the client
                await self.connection_closed(connection=connection)
                break

            if 'text' in response:
                await connection.receive(data=response['text'])
            else:
                await connection.receive(data=response['bytes'])

    async def connection_accepted(self, connection: Websocket) -> None:
        # Generate ConnectionID
        connection._connection_id = ULID.new()

        # Save Connection
        self.connections[connection.connection_id] = connection

        # Logs
        await connection.monitoring.after('Accepted')
        connection.log(f'Accepted {connection.connection_id}')

    async def connection_closed(self, connection: Websocket, from_server: bool = False) -> None:
        if connection.is_connected:
            del self.connections[connection.connection_id]
            await connection.monitoring.after('Closed')
            connection.log(f'Closed {connection.connection_id}')
            connection._connection_id = ''

        elif connection.is_rejected is False and from_server is True:
            await connection.monitoring.after('Rejected')
            connection.log('Rejected')
            connection._is_rejected = True

    async def start(self):
        """
        Start Websocket Listener (Redis/ Queue)

        Cause of --preload in gunicorn we have to keep this function here,
        and we can't move it to __init__ of Panther

            * Each process should start this listener for itself,
              but they have same Manager()
        """

        # Schedule the async function to run in the background,
        #   We don't need to await for this task
        asyncio.create_task(self())

    @classmethod
    async def handle_authentication(cls, connection: Websocket):
        """Return True if connection is closed, False otherwise."""
        if connection.auth:
            if not config.WS_AUTHENTICATION:
                logger.critical('`WS_AUTHENTICATION` has not been set in configs')
                await connection.close()
            else:
                try:
                    connection.user = await config.WS_AUTHENTICATION.authentication(connection)
                except AuthenticationAPIError as e:
                    connection.log(e.detail)
                    await connection.close()

    @classmethod
    async def handle_permissions(cls, connection: Websocket):
        """Return True if connection is closed, False otherwise."""
        for perm in connection.permissions:
            if type(perm.authorization).__name__ != 'method':
                logger.critical(f'{perm.__name__}.authorization should be "classmethod"')
                await connection.close()
            elif await perm.authorization(connection) is False:
                connection.log('Permission Denied')
                await connection.close()


class Websocket(BaseRequest):
    auth: bool = False
    permissions: list = []
    _connection_id: str = ''
    _is_rejected: bool = False
    _monitoring: Monitoring

    def __init_subclass__(cls, **kwargs):
        if cls.__module__ != 'panther.websocket':
            config.HAS_WS = True

    async def connect(self, **kwargs) -> None:
        pass

    async def receive(self, data: str | bytes) -> None:
        pass

    async def accept(self, subprotocol: str | None = None, headers: dict | None = None) -> None:
        await self.asgi_send({'type': 'websocket.accept', 'subprotocol': subprotocol, 'headers': headers or {}})
        await config.WEBSOCKET_CONNECTIONS.connection_accepted(connection=self)

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
        await self.asgi_send({'type': 'websocket.close', 'code': code, 'reason': reason})
        await config.WEBSOCKET_CONNECTIONS.connection_closed(connection=self, from_server=True)

    @property
    def connection_id(self) -> str:
        if self.is_connected:
            return self._connection_id
        logger.error('You should first `self.accept()` the connection then use the `self.connection_id`')

    @property
    def is_connected(self) -> bool:
        return bool(self._connection_id)

    @property
    def is_rejected(self) -> bool:
        return self._is_rejected

    @property
    def monitoring(self) -> Monitoring:
        return self._monitoring

    def log(self, message: str):
        logger.debug(f'WS {self.path} --> {message}')
