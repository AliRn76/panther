import logging
from unittest import IsolatedAsyncioTestCase

from panther.configs import config
from panther.events import Event

logger = logging.getLogger('panther')


class TestEvents(IsolatedAsyncioTestCase):
    def setUp(self):
        Event.clear()

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_async_startup(self):
        assert len(Event._startups) == 0

        async def startup_event():
            logger.info('This Is Startup.')

        Event.startup(startup_event)

        assert len(Event._startups) == 1
        assert Event._startups[0] == startup_event

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Startup.'

    async def test_sync_startup(self):
        assert len(Event._startups) == 0

        def startup_event():
            logger.info('This Is Startup.')

        Event.startup(startup_event)

        assert len(Event._startups) == 1
        assert Event._startups[0] == startup_event

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Startup.'

    async def test_startup(self):
        assert len(Event._startups) == 0

        def startup_event1():
            logger.info('This Is Startup1.')

        async def startup_event2():
            logger.info('This Is Startup2.')

        Event.startup(startup_event1)
        Event.startup(startup_event2)

        assert len(Event._startups) == 2
        assert Event._startups[0] == startup_event1
        assert Event._startups[1] == startup_event2

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 2
        assert capture.records[0].getMessage() == 'This Is Startup1.'
        assert capture.records[1].getMessage() == 'This Is Startup2.'

    async def test_sync_shutdown(self):
        assert len(Event._shutdowns) == 0

        def shutdown_event():
            logger.info('This Is Shutdown.')

        Event.shutdown(shutdown_event)

        assert len(Event._shutdowns) == 1
        assert Event._shutdowns[0] == shutdown_event

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Shutdown.'

    async def shutdown_event(self):
        logger.info('This Is Shutdown.')

    def test_async_shutdown(self):
        assert len(Event._shutdowns) == 0

        Event.shutdown(self.shutdown_event)

        assert len(Event._shutdowns) == 1
        assert Event._shutdowns[0] == self.shutdown_event

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Shutdown.'

    def test_shutdown(self):
        assert len(Event._shutdowns) == 0

        def shutdown_event_sync():
            logger.info('This Is Sync Shutdown.')

        Event.shutdown(self.shutdown_event)
        Event.shutdown(shutdown_event_sync)

        assert len(Event._shutdowns) == 2
        assert Event._shutdowns[0] == self.shutdown_event
        assert Event._shutdowns[1] == shutdown_event_sync

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 2
        assert capture.records[0].getMessage() == 'This Is Shutdown.'
        assert capture.records[1].getMessage() == 'This Is Sync Shutdown.'

    def test_singleton_pattern(self):
        """Test that Event class works as a singleton"""
        event1 = Event()
        event2 = Event()
        assert event1 is event2

        # Test that the same instance is used for storing events
        def test_func():
            pass

        Event.startup(test_func)
        assert len(Event._startups) == 1
        assert Event._startups[0] == test_func
