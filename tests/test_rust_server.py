import asyncio
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import patch

from panther import server as panther_server
from panther.cli.run_command import load_app, parse_rust_options, split_server_option
from panther.exceptions import PantherError

try:
    import websockets
except ImportError:
    websockets = None


class TestPackaging(TestCase):
    """`rust/` is a second top-level directory, which breaks setuptools' flat-layout
    auto-discovery unless `packages` is declared explicitly. Guard that here: the
    failure mode is an install that dies with "Multiple top-level packages
    discovered in a flat-layout".
    """

    @staticmethod
    def _setup_kwargs():
        import setuptools

        setup_py = Path(__file__).resolve().parent.parent / 'setup.py'
        captured = {}
        original = setuptools.setup
        setuptools.setup = lambda **kwargs: captured.update(kwargs)
        try:
            namespace = {'__name__': '__main__', '__file__': str(setup_py)}
            exec(compile(setup_py.read_text(), str(setup_py), 'exec'), namespace)  # noqa: S102
        finally:
            setuptools.setup = original
        return captured

    def test_packages_are_declared_explicitly(self):
        packages = self._setup_kwargs()['packages']
        assert 'panther' in packages
        assert [name for name in packages if name == 'rust' or name.startswith('rust.')] == []
        assert all(name == 'panther' or name.startswith('panther.') for name in packages)

    def test_subpackages_are_included(self):
        packages = set(self._setup_kwargs()['packages'])
        expected = {
            'panther.cli',
            'panther.db',
            'panther.db.queries',
            'panther.middlewares',
            'panther.openapi',
            'panther.panel',
        }
        assert expected <= packages

    def test_rust_extra_exists(self):
        extras = self._setup_kwargs()['extras_require']
        assert 'rust' in extras
        assert any('panther-server' in requirement for requirement in extras['rust'])


class TestSplitServerOption(TestCase):
    def test_default_is_uvicorn(self):
        server, args = split_server_option(['main:app', '--reload'])
        assert server == 'uvicorn'
        assert args == ['main:app', '--reload']

    def test_space_separated(self):
        server, args = split_server_option(['--server', 'rust', 'main:app'])
        assert server == 'rust'
        assert args == ['main:app']

    def test_equals_separated(self):
        server, args = split_server_option(['--server=rust', 'main:app'])
        assert server == 'rust'
        assert args == ['main:app']

    def test_other_options_are_preserved_in_order(self):
        server, args = split_server_option(['--host', '0.0.0.0', '--server', 'rust', 'main:app', '--port', '9000'])
        assert server == 'rust'
        assert args == ['--host', '0.0.0.0', 'main:app', '--port', '9000']

    def test_explicit_uvicorn(self):
        server, args = split_server_option(['--server', 'uvicorn', 'main:app'])
        assert server == 'uvicorn'
        assert args == ['main:app']

    def test_missing_value(self):
        with self.assertRaises(ValueError) as context:
            split_server_option(['main:app', '--server'])
        assert '`--server` requires a value' in str(context.exception)

    def test_unknown_server(self):
        with self.assertRaises(ValueError) as context:
            split_server_option(['--server', 'gunicorn', 'main:app'])
        assert "Unknown server 'gunicorn'" in str(context.exception)


class TestParseRustOptions(TestCase):
    def test_defaults(self):
        address, options = parse_rust_options(['main:app'])
        assert address == 'main:app'
        assert options == {
            'host': '127.0.0.1',
            'port': 8000,
            'root_path': '',
            'workers': None,
            'lifespan': True,
        }

    def test_all_options(self):
        address, options = parse_rust_options(
            ['main:app', '--host', '0.0.0.0', '--port', '9000', '--workers', '4', '--root-path', '/api'],
        )
        assert address == 'main:app'
        assert options['host'] == '0.0.0.0'
        assert options['port'] == 9000
        assert options['workers'] == 4
        assert options['root_path'] == '/api'

    def test_equals_form(self):
        address, options = parse_rust_options(['--port=9000', 'main:app'])
        assert address == 'main:app'
        assert options['port'] == 9000

    def test_no_lifespan(self):
        _, options = parse_rust_options(['main:app', '--no-lifespan'])
        assert options['lifespan'] is False

    def test_address_can_come_last(self):
        address, options = parse_rust_options(['--port', '9000', 'main:app'])
        assert address == 'main:app'
        assert options['port'] == 9000

    def test_missing_address(self):
        with self.assertRaises(ValueError) as context:
            parse_rust_options(['--port', '9000'])
        assert 'address of your application' in str(context.exception)

    def test_two_addresses(self):
        with self.assertRaises(ValueError) as context:
            parse_rust_options(['main:app', 'other:app'])
        assert 'Too many application addresses' in str(context.exception)

    def test_unsupported_option(self):
        with self.assertRaises(ValueError) as context:
            parse_rust_options(['main:app', '--reload'])
        assert 'not supported by the Rust server' in str(context.exception)

    def test_non_integer_port(self):
        with self.assertRaises(ValueError) as context:
            parse_rust_options(['main:app', '--port', 'http'])
        assert 'expects an integer' in str(context.exception)

    def test_option_without_value(self):
        with self.assertRaises(ValueError) as context:
            parse_rust_options(['main:app', '--port'])
        assert '`--port` requires a value' in str(context.exception)


class TestLoadApp(TestCase):
    def setUp(self):
        self._directory = TemporaryDirectory()
        self.path = Path(self._directory.name)
        (self.path / 'sample_asgi_module.py').write_text(
            textwrap.dedent(
                """
                class Holder:
                    inner = 'nested-app'

                app = 'top-level-app'
                holder = Holder()
                """,
            ),
        )
        sys.path.insert(0, str(self.path))

    def tearDown(self):
        sys.path.remove(str(self.path))
        sys.modules.pop('sample_asgi_module', None)
        self._directory.cleanup()

    def test_load(self):
        assert load_app('sample_asgi_module:app') == 'top-level-app'

    def test_load_dotted_attribute(self):
        assert load_app('sample_asgi_module:holder.inner') == 'nested-app'

    def test_load_strips_py_suffix(self):
        assert load_app('sample_asgi_module.py:app') == 'top-level-app'

    def test_address_without_colon(self):
        with self.assertRaises(ValueError) as context:
            load_app('sample_asgi_module')
        assert 'expected `module:attribute`' in str(context.exception)

    def test_unknown_module(self):
        with self.assertRaises(ValueError) as context:
            load_app('module_that_does_not_exist:app')
        assert 'Cannot import' in str(context.exception)

    def test_unknown_attribute(self):
        with self.assertRaises(ValueError) as context:
            load_app('sample_asgi_module:nope')
        assert 'has no attribute' in str(context.exception)


class TestExtensionLoading(TestCase):
    def test_load_extension_error_message(self):
        with patch.dict(sys.modules, {'panther_server': None}):
            with self.assertRaises(PantherError) as context:
                panther_server.load_extension()
        assert 'pip install panther[rust]' in context.exception.args[0]
        assert 'maturin develop' in context.exception.args[0]

    def test_available_is_false_without_extension(self):
        with patch.dict(sys.modules, {'panther_server': None}):
            assert panther_server.available() is False


class TestLifespanCycle(IsolatedAsyncioTestCase):
    async def test_startup_and_shutdown(self):
        events = []

        async def app(scope, receive, send):
            assert scope['type'] == 'lifespan'
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    events.append('startup')
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    events.append('shutdown')
                    await send({'type': 'lifespan.shutdown.complete'})
                    return

        cycle = panther_server.LifespanCycle(app)
        await cycle.startup()
        assert events == ['startup']
        await cycle.shutdown()
        assert events == ['startup', 'shutdown']
        assert cycle.error is None

    async def test_startup_failure_raises(self):
        async def app(scope, receive, send):
            await receive()
            await send({'type': 'lifespan.startup.failed', 'message': 'database is down'})

        cycle = panther_server.LifespanCycle(app)
        with self.assertRaises(PantherError) as context:
            await cycle.startup()
        assert 'database is down' in context.exception.args[0]

    async def test_unsupported_lifespan_does_not_raise(self):
        async def app(scope, receive, send):
            raise NotImplementedError('no lifespan here')

        cycle = panther_server.LifespanCycle(app)
        await cycle.startup()
        assert cycle.supported is False
        # Shutdown is a no-op rather than a hang when the app never listened.
        await cycle.shutdown()


class FakeConnection:
    """Stands in for the Rust `Connection` so the Python driver can be tested alone."""

    def __init__(self, scope, incoming):
        self.scope = scope
        self.kind = scope['type']
        self._incoming = list(incoming)
        self.sent = []

    async def receive(self):
        if self._incoming:
            return self._incoming.pop(0)
        await asyncio.sleep(3600)  # mimic a connection with nothing more to say

    async def send(self, message):
        self.sent.append(message)


class FakeServer:
    instances = []

    def __init__(self, host, port, *, root_path='', backlog=1024, message_buffer=32):
        self.host = host
        self.port = port
        self.root_path = root_path
        self.backlog = backlog
        self.message_buffer = message_buffer
        self.started = False
        self.shutdown_called = False
        self.pending = []
        FakeServer.instances.append(self)

    async def start(self):
        self.started = True
        return (self.host, self.port)

    async def accept(self):
        if self.pending:
            return self.pending.pop(0)
        return None

    async def shutdown(self):
        self.shutdown_called = True


class FakeExtension:
    """Stands in for the compiled `panther_server` module."""

    def __init__(self, *connections):
        self.configured_with = None
        self.Server = self._build_server(connections)

    @staticmethod
    def _build_server(connections):
        def factory(host, port, **kwargs):
            server = FakeServer(host, port, **kwargs)
            server.pending = list(connections)
            return server

        return factory

    def configure_runtime(self, worker_threads=None):
        self.configured_with = worker_threads
        return True


class TestServe(IsolatedAsyncioTestCase):
    def setUp(self):
        FakeServer.instances = []

    @staticmethod
    def _serving(extension):
        return patch.object(panther_server, 'load_extension', return_value=extension)

    async def test_drives_the_application(self):
        connection = FakeConnection(
            {'type': 'http', 'path': '/'},
            [{'type': 'http.request', 'body': b'', 'more_body': False}],
        )

        async def app(scope, receive, send):
            await receive()
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'ok', 'more_body': False})

        extension = FakeExtension(connection)
        with self._serving(extension):
            await panther_server.serve(app, port=0, workers=2, lifespan=False)

        assert [message['type'] for message in connection.sent] == [
            'http.response.start',
            'http.response.body',
        ]
        assert extension.configured_with == 2
        assert FakeServer.instances[0].started is True
        assert FakeServer.instances[0].shutdown_called is True

    async def test_failing_endpoint_does_not_stop_the_server(self):
        first = FakeConnection({'type': 'http', 'path': '/boom'}, [])
        second = FakeConnection(
            {'type': 'http', 'path': '/'},
            [{'type': 'http.request', 'body': b'', 'more_body': False}],
        )
        handled = []

        async def app(scope, receive, send):
            if scope['path'] == '/boom':
                raise RuntimeError('endpoint exploded')
            handled.append(scope['path'])

        with self._serving(FakeExtension(first, second)):
            await panther_server.serve(app, port=0, lifespan=False)

        assert handled == ['/']

    async def test_options_reach_the_extension(self):
        async def app(scope, receive, send):
            pass

        with self._serving(FakeExtension()):
            await panther_server.serve(
                app,
                host='0.0.0.0',
                port=1234,
                root_path='/api',
                backlog=16,
                message_buffer=4,
                lifespan=False,
            )

        server = FakeServer.instances[0]
        assert (server.host, server.port) == ('0.0.0.0', 1234)
        assert server.root_path == '/api'
        assert server.backlog == 16
        assert server.message_buffer == 4

    async def test_lifespan_runs_around_the_server(self):
        events = []

        async def app(scope, receive, send):
            if scope['type'] != 'lifespan':
                return
            while True:
                message = await receive()
                events.append(message['type'])
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                else:
                    await send({'type': 'lifespan.shutdown.complete'})
                    return

        with self._serving(FakeExtension()):
            await panther_server.serve(app, port=0)

        assert events == ['lifespan.startup', 'lifespan.shutdown']


@skipUnless(panther_server.available(), 'the `panther-server` Rust extension is not installed')
class TestRustServerEndToEnd(IsolatedAsyncioTestCase):
    """Exercises the compiled extension over a real socket; skipped on a pure-Python checkout."""

    async def asyncSetUp(self):
        self.seen = []
        ready = asyncio.get_running_loop().create_future()

        async def app(scope, receive, send):
            if scope['type'] == 'lifespan':
                while True:
                    message = await receive()
                    await send({'type': f'{message["type"]}.complete'})
                    if message['type'] == 'lifespan.shutdown':
                        return

            body = b''
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                body += message.get('body', b'')
                if not message.get('more_body', False):
                    break

            self.seen.append(
                {
                    'method': scope['method'],
                    'path': scope['path'],
                    'query_string': scope['query_string'],
                    'body': body,
                    'headers': dict(scope['headers']),
                },
            )
            await send(
                {
                    'type': 'http.response.start',
                    'status': 201,
                    'headers': [(b'content-type', b'text/plain'), (b'content-length', b'5')],
                },
            )
            await send({'type': 'http.response.body', 'body': b'hello', 'more_body': False})

        def on_ready(host, port):
            if not ready.done():
                ready.set_result((host, port))

        self.task = asyncio.ensure_future(
            panther_server.serve(app, host='127.0.0.1', port=0, on_ready=on_ready),
        )
        self.host, self.port = await asyncio.wait_for(ready, timeout=10)

    async def asyncTearDown(self):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def _request(self, raw: bytes) -> bytes:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        writer.write(raw)
        await writer.drain()
        response = await asyncio.wait_for(reader.read(-1), timeout=10)
        writer.close()
        return response

    async def test_get_roundtrip(self):
        response = await self._request(
            b'GET /users?page=2 HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n',
        )

        assert response.startswith(b'HTTP/1.1 201')
        assert response.endswith(b'hello')
        assert b'content-type: text/plain' in response.lower()

        assert len(self.seen) == 1
        request = self.seen[0]
        assert request['method'] == 'GET'
        assert request['path'] == '/users'
        assert request['query_string'] == b'page=2'
        assert request['body'] == b''
        assert request['headers'][b'host'] == b'localhost'

    async def test_post_body_is_delivered(self):
        response = await self._request(
            b'POST /items HTTP/1.1\r\nHost: localhost\r\nContent-Length: 7\r\nConnection: close\r\n\r\npayload',
        )

        assert response.startswith(b'HTTP/1.1 201')
        assert self.seen[0]['body'] == b'payload'

    async def test_percent_encoded_path_is_decoded(self):
        await self._request(b'GET /a%20b HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
        assert self.seen[0]['path'] == '/a b'


@skipUnless(panther_server.available(), 'the `panther-server` Rust extension is not installed')
class TestRustServerWebsocket(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        ready = asyncio.get_running_loop().create_future()
        self.scopes = []
        self.received = []

        async def app(scope, receive, send):
            if scope['type'] != 'websocket':
                return

            self.scopes.append(scope)
            assert (await receive())['type'] == 'websocket.connect'
            await send({'type': 'websocket.accept', 'subprotocol': None, 'headers': {}})

            while True:
                message = await receive()
                if message['type'] == 'websocket.disconnect':
                    return
                self.received.append(message)
                # Dispatch the way Panther's `listen_connection()` does, so a
                # message carrying both keys would route a binary frame down
                # the text branch and fail loudly.
                if 'text' in message:
                    await send({'type': 'websocket.send', 'text': message['text'].upper()})
                else:
                    await send({'type': 'websocket.send', 'bytes': message['bytes'][::-1]})

        def on_ready(host, port):
            if not ready.done():
                ready.set_result((host, port))

        self.task = asyncio.ensure_future(
            panther_server.serve(app, host='127.0.0.1', port=0, lifespan=False, on_ready=on_ready),
        )
        self.host, self.port = await asyncio.wait_for(ready, timeout=10)

    async def asyncTearDown(self):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    @skipUnless(websockets is not None, 'the `websockets` package is not installed')
    async def test_echo(self):
        async with websockets.connect(f'ws://{self.host}:{self.port}/ws/room') as connection:
            await connection.send('ping')
            assert await connection.recv() == 'PING'
            await connection.send(b'\x01\x02')
            assert await connection.recv() == b'\x02\x01'

        assert self.scopes[0]['path'] == '/ws/room'
        assert self.scopes[0]['type'] == 'websocket'
        # Websocket scopes carry no `method`, matching uvicorn and Panther's
        # own `WebsocketClient`.
        assert 'method' not in self.scopes[0]

        # Exactly one of the two payload keys per message, never both.
        assert [sorted(set(m) & {'text', 'bytes'}) for m in self.received] == [['text'], ['bytes']]


class TestExtensionLinking(TestCase):
    """A bare `cargo build` inside `rust/` must link on macOS.

    `pyo3`'s `extension-module` feature leaves CPython's symbols undefined for the
    interpreter to resolve at import time. Mach-O rejects that unless the linker is
    told to look them up dynamically, so without `build.rs` every macOS build dies
    with "Undefined symbols for architecture arm64". `maturin` passes the flag on
    its own, which is why this only bites contributors who run cargo directly.
    """

    BUILD_SCRIPT = Path(__file__).resolve().parent.parent / 'rust' / 'build.rs'

    @classmethod
    def _code(cls) -> str:
        """The build script with its comments stripped.

        The comments deliberately name `cfg!(target_os = ...)` to explain why it is
        the wrong tool here, so a substring check over the raw file finds the very
        thing it is meant to forbid.
        """
        return '\n'.join(
            line for line in cls.BUILD_SCRIPT.read_text().splitlines() if not line.lstrip().startswith('//')
        )

    def test_build_script_exists(self):
        assert self.BUILD_SCRIPT.is_file()

    def test_macos_gets_dynamic_lookup(self):
        assert 'cargo:rustc-cdylib-link-arg=-Wl,-undefined,dynamic_lookup' in self._code()

    def test_flag_is_gated_on_the_target_not_the_host(self):
        code = self._code()
        assert 'CARGO_CFG_TARGET_OS' in code
        assert 'cfg!(target_os' not in code
