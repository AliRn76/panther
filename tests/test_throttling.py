import asyncio
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API
from panther.configs import config
from panther.test import APIClient
from panther.throttling import Throttle
from panther.utils import round_datetime


@API()
async def without_throttling_api():
    return 'ok'


@API(throttling=Throttle(rate=3, duration=timedelta(seconds=1)))
async def with_throttling_api():
    return 'ok'


@API(throttling=Throttle(rate=1, duration=timedelta(seconds=1)))
async def throttling_headers_api():
    return 'ok'


THROTTLING = Throttle(rate=1, duration=timedelta(seconds=10))

urls = {
    'without-throttling': without_throttling_api,
    'with-throttling': with_throttling_api,
    'throttling-headers': throttling_headers_api,
}


class TestThrottling(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_without_throttling(self):
        throttling = config.THROTTLING
        config.THROTTLING = None  # Disable Global Throttling

        res1 = await self.client.get('without-throttling')
        assert res1.status_code == 200

        res2 = await self.client.get('without-throttling')
        assert res2.status_code == 200

        res3 = await self.client.get('without-throttling')
        assert res3.status_code == 200
        config.THROTTLING = throttling

    async def test_with_throttling(self):
        res1 = await self.client.get('with-throttling')
        assert res1.status_code == 200

        res2 = await self.client.get('with-throttling')
        assert res2.status_code == 200

        res3 = await self.client.get('with-throttling')
        assert res3.status_code == 200

        res4 = await self.client.get('with-throttling')
        assert res4.status_code == 429

        res5 = await self.client.get('with-throttling')
        assert res5.status_code == 429

        await asyncio.sleep(1)  # Sleep and try again

        res6 = await self.client.get('with-throttling')
        assert res6.status_code == 200

        res7 = await self.client.get('with-throttling')
        assert res7.status_code == 200

        res8 = await self.client.get('with-throttling')
        assert res8.status_code == 200

        res9 = await self.client.get('with-throttling')
        assert res9.status_code == 429

        res10 = await self.client.get('with-throttling')
        assert res10.status_code == 429

    async def test_throttling_header(self):
        await self.client.get('throttling-headers')

        res = await self.client.get('throttling-headers')
        assert res.status_code == 429
        reset_time = round_datetime(datetime.now(), timedelta(seconds=1)) + timedelta(seconds=1)
        assert res.headers == {
            'Content-Type': 'application/json',
            'Content-Length': '29',
            'Retry-After': str(int((reset_time - datetime.now()).total_seconds())),
            'X-RateLimit-Reset': str(int(reset_time.timestamp())),
        }

    async def test_global_throttling(self):
        res1 = await self.client.get('without-throttling')
        assert res1.status_code == 200

        res2 = await self.client.get('without-throttling')
        assert res2.status_code == 429
