import asyncio
import multiprocessing
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from multiprocessing.managers import SyncManager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless

from panther import Panther
from panther.base_websocket import PubSub, WebsocketConnections, create_pubsub_manager
from panther.configs import config
from panther.test import WebsocketClient
from panther.websocket import GenericWebsocket

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Long enough that a slow machine won't fail, short enough that a regression fails instead of hanging.
SUBPROCESS_TIMEOUT = 60
CONNECT_TIMEOUT = 20
WORKER_TIMEOUT = 30


class StaysOpenWebsocket(GenericWebsocket):
    """Accepts and keeps the connection open, i.e. what a real endpoint does."""

    async def connect(self):
        await self.accept()
        await self.send('open')


class TestWebsocketClientTerminates(TestCase):
    """
    `WebsocketClient` used to answer every `receive()` with `websocket.connect`, which
    `listen_connection()` skips with `continue`, so any endpoint that accepted without closing left
    the client spinning forever. Endpoints that call `close()` inside `connect()` never reached that
    loop, which is why this went unnoticed.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = Panther(__name__, configs=__name__, urls={'ws/open/': StaysOpenWebsocket})

    def connect(self, client: WebsocketClient, path: str) -> list:
        """
        Run `connect()` off-thread so a regression fails on a timeout rather than hanging the suite.
        `connect()` runs its own event loop, so a worker thread is safe.
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(client.connect, path)
            try:
                return future.result(timeout=CONNECT_TIMEOUT)
            except FutureTimeoutError:
                self.fail(
                    f'WebsocketClient.connect() did not return within {CONNECT_TIMEOUT}s. '
                    'It is most likely spinning on `websocket.connect` again.',
                )

    def test_connect_returns_for_an_endpoint_that_stays_open(self):
        messages = self.connect(WebsocketClient(app=self.app), '/ws/open/')

        self.assertEqual(messages[0]['type'], 'websocket.accept')
        self.assertEqual(messages[1]['text'], 'open')

    def test_repeated_connects_do_not_accumulate_messages(self):
        client = WebsocketClient(app=self.app)

        first = self.connect(client, '/ws/open/')
        second = self.connect(client, '/ws/open/')

        self.assertEqual(len(first), len(second))
        self.assertEqual(second[0]['type'], 'websocket.accept')


class TestPubsubManagerGuard(TestCase):
    """
    Covers the branch that only Windows reaches at runtime. Everywhere `fork` exists, the fork context
    is used and the guard never triggers, so exercise it directly rather than leaving it untested.
    """

    def setUp(self):
        # `WebsocketConnections` is a `Singleton`, so building one here would otherwise overwrite the
        # instance another test class installed on `config`.
        self._previous_connections = WebsocketConnections._instances.pop(WebsocketConnections, None)

    def tearDown(self):
        WebsocketConnections._instances.pop(WebsocketConnections, None)
        if self._previous_connections is not None:
            WebsocketConnections._instances[WebsocketConnections] = self._previous_connections

    def test_manager_is_created_outside_a_reimporting_child(self):
        manager = create_pubsub_manager()
        self.addCleanup(manager.shutdown)

        self.assertIsInstance(manager, SyncManager)

    def test_no_manager_while_a_spawned_child_reimports_the_main_module(self):
        process = multiprocessing.current_process()
        process._inheriting = True
        try:
            self.assertIsNone(create_pubsub_manager())
        finally:
            del process._inheriting

    def test_connections_without_a_pubsub_neither_listens_nor_crashes(self):
        connections = WebsocketConnections(pubsub_connection=None)

        self.assertIsNone(connections.pubsub)
        # Both are no-ops rather than an AttributeError: this only exists in a process that serves the
        # manager and exits without handling a connection.
        asyncio.run(connections())
        asyncio.run(connections.publish(connection_id='missing', action='send', data='ignored'))

    def test_reconstructing_replaces_the_pubsub_of_the_shared_instance(self):
        """
        `Singleton.__new__` caches per class but `__init__` still runs on every call, so a second
        `WebsocketConnections(...)` rebinds the pubsub of the object everyone already holds. Pinned
        here because it is the trap behind building more than one app in a single process.
        """
        manager = create_pubsub_manager()
        self.addCleanup(manager.shutdown)

        first = WebsocketConnections(pubsub_connection=manager)
        self.assertIsNotNone(first.pubsub)

        second = WebsocketConnections(pubsub_connection=None)

        self.assertIs(second, first)
        self.assertIsNone(first.pubsub)


def _subscribe_then_report(pubsub, subscribed, results, timeout):
    """Stands in for a Gunicorn `--preload` worker: fork first, then subscribe."""
    try:
        queue = pubsub.subscribe()
        subscribed.set()
        results.put(queue.get(timeout=timeout))
    except Exception as e:  # noqa: BLE001 - the parent asserts on whatever arrives
        subscribed.set()
        results.put(f'error: {e!r}')


@skipUnless('fork' in multiprocessing.get_all_start_methods(), 'Requires the `fork` start method')
class TestPubsubReachesForkedWorkers(TestCase):
    """
    The reason the manager is built while configs load, rather than lazily at startup: Gunicorn
    `--preload` imports the app in the master and forks workers afterwards, so every worker inherits
    one manager and a publish from any of them reaches all the others. Nothing covered that, so a
    change making creation lazy would have broken multi-worker websockets silently.
    """

    WORKER_COUNT = 2

    def test_a_manager_built_before_forking_fans_out_to_every_worker(self):
        manager = create_pubsub_manager()
        self.addCleanup(manager.shutdown)
        pubsub = PubSub(manager=manager)

        context = multiprocessing.get_context('fork')
        results = context.Queue()
        workers = []
        for _ in range(self.WORKER_COUNT):
            subscribed = context.Event()
            worker = context.Process(
                target=_subscribe_then_report,
                args=(pubsub, subscribed, results, WORKER_TIMEOUT),
            )
            worker.start()
            self.addCleanup(worker.terminate)
            self.assertTrue(subscribed.wait(timeout=WORKER_TIMEOUT), 'A forked worker never subscribed.')
            workers.append(worker)

        message = {'connection_id': 'abc', 'action': 'send', 'data': 'hello'}
        pubsub.publish(message)

        received = [results.get(timeout=WORKER_TIMEOUT) for _ in workers]

        self.assertEqual(received, [message] * self.WORKER_COUNT)
        for worker in workers:
            worker.join(timeout=WORKER_TIMEOUT)
            self.assertEqual(worker.exitcode, 0)


class TestManagerExistsBeforeStartup(TestCase):
    """
    Fan-out above only holds if the manager is already there when Gunicorn forks, i.e. built during
    `Panther(...)` rather than during the lifespan startup that each worker runs for itself.
    """

    def test_building_an_app_creates_the_manager(self):
        previous = WebsocketConnections._instances.pop(WebsocketConnections, None)
        self.addCleanup(
            lambda: (
                WebsocketConnections._instances.__setitem__(WebsocketConnections, previous)
                if previous is not None
                else WebsocketConnections._instances.pop(WebsocketConnections, None)
            ),
        )

        Panther(__name__, configs=__name__, urls={'ws/startup/': StaysOpenWebsocket})

        connections = config.WEBSOCKET_CONNECTIONS
        self.addCleanup(connections.pubsub_connection.shutdown)

        self.assertIsInstance(connections.pubsub_connection, SyncManager)
        self.assertIsNotNone(connections.pubsub)


class TestWebsocketAppStartsInASubprocess(TestCase):
    """
    Without Redis, websocket pubsub is backed by a `multiprocessing.Manager`. Under the `spawn` start
    method the manager process re-imports the main module, rebuilding the app and asking for a second
    manager, which CPython aborts. Guarding that relies on a private CPython attribute
    (`_inheriting`), so assert the observable behavior — a module-level websocket app in a directly
    executed script has to start and exit cleanly.
    """

    SCRIPT = textwrap.dedent(
        """
        from panther import Panther
        from panther.test import WebsocketClient
        from panther.websocket import GenericWebsocket

        SECRET_KEY = 'websocket-lifecycle-test'


        class HelloWebsocket(GenericWebsocket):
            async def connect(self):
                await self.accept()
                await self.send('hello')


        url_routing = {'ws/hello/': HelloWebsocket}

        app = Panther(__name__, configs=__name__, urls=url_routing)

        if __name__ == '__main__':
            messages = WebsocketClient(app=app).connect('/ws/hello/')
            assert messages[0]['type'] == 'websocket.accept', messages
            assert messages[1]['text'] == 'hello', messages
            print('OK')
        """,
    )

    def test_script_with_a_module_level_websocket_app_exits_cleanly(self):
        with TemporaryDirectory() as directory:
            script = Path(directory) / 'ws_app.py'
            script.write_text(self.SCRIPT)

            try:
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True,
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT,
                    cwd=str(PROJECT_ROOT),
                )
            except subprocess.TimeoutExpired:
                self.fail(
                    f'A websocket app did not finish within {SUBPROCESS_TIMEOUT}s. '
                    'The pubsub manager is most likely recursing through the main module again.',
                )

        self.assertEqual(result.returncode, 0, f'stdout={result.stdout}\nstderr={result.stderr}')
        self.assertIn('OK', result.stdout)
        self.assertNotIn('bootstrapping phase', result.stderr)
