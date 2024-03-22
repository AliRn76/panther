import logging
from unittest import IsolatedAsyncioTestCase

from panther.configs import config
from panther.events import Event

logger = logging.getLogger('panther')


class TestEvents(IsolatedAsyncioTestCase):
    def tearDown(self):
        config.refresh()

    async def test_async_startup(self):
        assert len(config.STARTUPS) == 0

        async def startup_event():
            logger.info('This Is Startup.')

        Event.startup(startup_event)

        assert len(config.STARTUPS) == 1
        assert config.STARTUPS[0] == startup_event

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Startup.'

    async def test_sync_startup(self):
        assert len(config.STARTUPS) == 0

        def startup_event():
            logger.info('This Is Startup.')

        Event.startup(startup_event)

        assert len(config.STARTUPS) == 1
        assert config.STARTUPS[0] == startup_event

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Startup.'

    async def test_startup(self):
        assert len(config.STARTUPS) == 0

        def startup_event1():
            logger.info('This Is Startup1.')

        async def startup_event2():
            logger.info('This Is Startup2.')

        Event.startup(startup_event1)
        Event.startup(startup_event2)

        assert len(config.STARTUPS) == 2
        assert config.STARTUPS[0] == startup_event1
        assert config.STARTUPS[1] == startup_event2

        with self.assertLogs(level='INFO') as capture:
            await Event.run_startups()

        assert len(capture.records) == 2
        assert capture.records[0].getMessage() == 'This Is Startup1.'
        assert capture.records[1].getMessage() == 'This Is Startup2.'

    async def test_sync_shutdown(self):
        assert len(config.SHUTDOWNS) == 0

        def shutdown_event():
            logger.info('This Is Shutdown.')

        Event.shutdown(shutdown_event)

        assert len(config.SHUTDOWNS) == 1
        assert config.SHUTDOWNS[0] == shutdown_event

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Shutdown.'

    async def shutdown_event(self):
        logger.info('This Is Shutdown.')

    def test_async_shutdown(self):
        assert len(config.SHUTDOWNS) == 0

        Event.shutdown(self.shutdown_event)

        assert len(config.SHUTDOWNS) == 1
        assert config.SHUTDOWNS[0] == self.shutdown_event

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 1
        assert capture.records[0].getMessage() == 'This Is Shutdown.'

    def test_shutdown(self):
        assert len(config.SHUTDOWNS) == 0

        def shutdown_event_sync():
            logger.info('This Is Sync Shutdown.')

        Event.shutdown(self.shutdown_event)
        Event.shutdown(shutdown_event_sync)

        assert len(config.SHUTDOWNS) == 2
        assert config.SHUTDOWNS[0] == self.shutdown_event
        assert config.SHUTDOWNS[1] == shutdown_event_sync

        with self.assertLogs(level='INFO') as capture:
            Event.run_shutdowns()

        assert len(capture.records) == 2
        assert capture.records[0].getMessage() == 'This Is Shutdown.'
        assert capture.records[1].getMessage() == 'This Is Sync Shutdown.'
