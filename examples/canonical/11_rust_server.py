"""Running a Panther app on the optional Rust web server (hyper + tokio).

The application below is ordinary Panther — nothing about an endpoint changes
when you switch servers. Only the way the process is started differs.

    pip install panther[rust]

    # From the CLI
    panther run --server rust examples.canonical.11_rust_server:app

    # Or run this file directly, which uses `panther.server.run()` below
    python -m examples.canonical.11_rust_server

Then:

    curl http://127.0.0.1:8000/hello/
    curl -X POST -d '{"name": "Ali"}' http://127.0.0.1:8000/echo/
"""

from panther import Panther, status
from panther.app import API
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


@API()
async def hello():
    return Response(
        data={'message': 'Hello from Panther on the Rust web server'},
        status_code=status.HTTP_200_OK,
    )


@API()
async def echo(request: Request):
    # Request bodies are streamed in from hyper and reassembled by Panther,
    # exactly as they are under Uvicorn.
    return Response(data={'you_sent': request.data}, status_code=status.HTTP_200_OK)


class EchoWebsocket(GenericWebsocket):
    # Websockets work on the Rust server too: hyper performs the upgrade and
    # the frames are bridged to the usual ASGI messages.
    async def connect(self):
        await self.accept()
        await self.send('Connected to Panther WebSocket')

    async def receive(self, data: str | bytes):
        await self.send(f'Echo: {data}')


url_routing = {
    'hello/': hello,
    'echo/': echo,
    'ws/echo/': EchoWebsocket,
}

app = Panther(__name__, configs=__name__, urls=url_routing)


if __name__ == '__main__':
    from panther.exceptions import PantherError
    from panther.server import run

    try:
        # `workers` sets tokio worker threads inside this one process, so
        # websocket connections stay in shared memory.
        run(app, host='127.0.0.1', port=8000, workers=4)
    except PantherError as error:
        # Raised when the `panther-server` extension is not installed.
        print(error.args[0] if error.args else error)
