import asyncio
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API
from panther.test import APIClient
from panther.throttling import Throttling


@API()
async def without_throttling_api():
    return 'ok'


@API(throttling=Throttling(rate=3, duration=timedelta(seconds=3)))
async def with_throttling_api():
    return 'ok'


urls = {
    'without-throttling': without_throttling_api,
    'with-throttling': with_throttling_api,
}


class TestThrottling(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    async def test_without_throttling(self):
        res1 = await self.client.get('without-throttling')
        assert res1.status_code == 200

        res2 = await self.client.get('without-throttling')
        assert res2.status_code == 200

        res3 = await self.client.get('without-throttling')
        assert res3.status_code == 200

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

        await asyncio.sleep(3)  # Sleep and try again

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
