import asyncio
from collections.abc import Callable
from typing import Literal

import orjson as json

from panther.response import Response

__all__ = ('APIClient', 'WebsocketClient')


class RequestClient:
    def __init__(self, app: Callable):
        self.app = app

    async def send(self, data: dict):
        if data['type'] == 'http.response.start':
            self.header = data
        else:
            self.response = data

    async def receive(self):
        return {
            'type': 'http.request',
            'body': self.payload,
            'more_body': False,
        }

    async def request(
            self,
            path: str,
            method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
            payload: bytes | dict | None,
            headers: dict,
            query_params: dict,
    ) -> Response:
        headers = [(k.encode(), str(v).encode()) for k, v in headers.items()]
        if not path.startswith('/'):
            path = f'/{path}'

        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload)
        query_params = '&'.join(f'{k}={v}' for k, v in query_params.items())
        scope = {
            'type': 'http',
            'client': ('127.0.0.1', 8585),
            'headers': headers,
            'method': method,
            'path': path,
            'raw_path': path.encode(),
            'query_string': query_params.encode(),
        }
        await self.app(
            scope=scope,
            receive=self.receive,
            send=self.send,
        )
        return Response(
            data=json.loads(self.response.get('body', b'null')),
            status_code=self.header['status'],
            headers=self.header['headers'],
        )


class APIClient:
    def __init__(self, app: Callable):
        self._app = app

    def _send_request(
            self,
            path: str,
            method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
            payload: dict | None,
            headers: dict,
            query_params: dict,
    ) -> Response:
        request_client = RequestClient(app=self._app)
        return asyncio.run(
            request_client.request(
                path=path,
                method=method,
                payload=payload,
                headers=headers,
                query_params=query_params or {},
            )
        )

    def get(
            self,
            path: str,
            headers: dict | None = None,
            query_params: dict | None = None,
    ) -> Response:
        return self._send_request(
            path=path,
            method='GET',
            payload=None,
            headers=headers or {},
            query_params=query_params or {},
        )

    def post(
            self,
            path: str,
            payload: bytes | dict | None = None,
            headers: dict | None = None,
            query_params: dict | None = None,
            content_type: str = 'application/json',
    ) -> Response:
        headers = {'content-type': content_type} | (headers or {})
        return self._send_request(
            path=path,
            method='POST',
            payload=payload,
            headers=headers,
            query_params=query_params or {},
        )

    def put(
            self,
            path: str,
            payload: bytes | dict | None = None,
            headers: dict | None = None,
            query_params: dict | None = None,
            content_type: Literal['application/json', 'multipart/form-data'] = 'application/json',
    ) -> Response:
        headers = {'content-type': content_type} | (headers or {})
        return self._send_request(
            path=path,
            method='PUT',
            payload=payload,
            headers=headers,
            query_params=query_params or {},
        )

    def patch(
            self,
            path: str,
            payload: bytes | dict | None = None,
            headers: dict | None = None,
            query_params: dict | None = None,
            content_type: Literal['application/json', 'multipart/form-data'] = 'application/json',
    ) -> Response:
        headers = {'content-type': content_type} | (headers or {})
        return self._send_request(
            path=path,
            method='PATCH',
            payload=payload,
            headers=headers,
            query_params=query_params or {},
        )

    def delete(
            self,
            path: str,
            headers: dict | None = None,
            query_params: dict | None = None,
    ) -> Response:
        return self._send_request(
            path=path,
            method='DELETE',
            payload=None,
            headers=headers or {},
            query_params=query_params or {},
        )


class WebsocketClient:
    def __init__(self, app: Callable):
        self.app = app
        self.responses = []

    async def send(self, data: dict):
        self.responses.append(data)

    async def receive(self):
        return {
            'type': 'websocket.connect'
        }

    def connect(
            self,
            path: str,
            headers: dict | None = None,
            query_params: dict | None = None,
    ):
        headers = [(k.encode(), str(v).encode()) for k, v in (headers or {}).items()]
        if not path.startswith('/'):
            path = f'/{path}'

        query_params = '&'.join(f'{k}={v}' for k, v in (query_params or {}).items())
        scope = {
            'type': 'websocket',
            'asgi': {'version': '3.0', 'spec_version': '2.3'},
            'http_version': '1.1',
            'scheme': 'ws',
            'server': ('127.0.0.1', 8000),
            'client': ('127.0.0.1', 55330),
            'path': path,
            'raw_path': path.encode(),
            'query_string': query_params.encode(),
            'headers': headers,
            'subprotocols': [],
            'state': {}
        }
        asyncio.run(
            self.app(
                scope=scope,
                receive=self.receive,
                send=self.send,
            )
        )
        return self.responses
