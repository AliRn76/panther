import asyncio
from threading import Event, Thread
from unittest import TestCase

import panther.background_tasks as background_tasks
from panther.background_tasks import BackgroundTask


def _set_application_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    if hasattr(background_tasks, 'register_application_event_loop'):
        background_tasks.register_application_event_loop(loop)
    else:
        setattr(background_tasks, '_application_event_loop', loop)


async def _create_loop_bound_future(loop: asyncio.AbstractEventLoop) -> asyncio.Future:
    return loop.create_future()


class TestBackgroundTaskEventLoopIsolation(TestCase):
    def test_async_background_task_avoids_event_loop_mismatch(self):
        previous_loop = getattr(background_tasks, '_application_event_loop', None)
        app_loop = asyncio.new_event_loop()
        app_loop_ready = Event()
        app_loop_closed = Event()

        def run_application_loop():
            asyncio.set_event_loop(app_loop)
            app_loop_ready.set()
            app_loop.run_forever()
            app_loop.close()
            app_loop_closed.set()

        loop_thread = Thread(target=run_application_loop, daemon=True)
        loop_thread.start()
        assert app_loop_ready.wait(timeout=1), 'Application event loop did not start in time.'

        try:
            _set_application_loop(app_loop)
            loop_bound_future = asyncio.run_coroutine_threadsafe(_create_loop_bound_future(app_loop), app_loop).result(
                timeout=1
            )
            results = []

            async def consume_loop_bound_future(_results):
                await loop_bound_future
                _results.append('completed')

            app_loop.call_soon_threadsafe(app_loop.call_later, 0.01, loop_bound_future.set_result, 'ok')
            BackgroundTask(consume_loop_bound_future, results)()

            assert results == ['completed']
        finally:
            _set_application_loop(previous_loop)
            app_loop.call_soon_threadsafe(app_loop.stop)
            loop_thread.join(timeout=1)
            assert app_loop_closed.wait(timeout=1), 'Application event loop did not stop in time.'
