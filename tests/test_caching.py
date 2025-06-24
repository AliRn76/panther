import asyncio
import time
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase

import pytest

from panther import Panther
from panther.app import API
from panther.configs import config
from panther.response import HTMLResponse
from panther.test import APIClient


@API()
async def without_cache_api():
    await asyncio.sleep(0.01)
    return {'detail': time.time()}


@API(cache=timedelta(seconds=2))
async def expired_cache_api():
    await asyncio.sleep(0.01)
    return {'detail': time.time()}


@API(cache=timedelta(seconds=2))
async def expired_cache_html_response():
    await asyncio.sleep(0.01)
    return HTMLResponse(data=f'<html>{time.time()}</html>')


urls = {
    'without-cache': without_cache_api,
    'with-expired-cache': expired_cache_api,
    'with-html-response-cache': expired_cache_html_response,
}


@pytest.mark.slow
class TestInMemoryCaching(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_without_cache(self):
        res1 = await self.client.get('without-cache')
        assert res1.status_code == 200

        res2 = await self.client.get('without-cache')
        assert res2.status_code == 200

        assert res1.data != res2.data

    async def test_with_cache_5second_exp_time(self):
        # First Request
        with self.assertLogs(level='INFO') as captured:
            res1 = await self.client.get('with-expired-cache')
        assert res1.status_code == 200

        # Check Logs
        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == '`cache` is not very accurate when `redis` is not connected.'

        # Second Request
        res2 = await self.client.get('with-expired-cache')
        assert res2.status_code == 200

        # Response should be cached
        assert res1.data == res2.data

        await asyncio.sleep(2)

        # Third Request
        res3 = await self.client.get('with-expired-cache')
        assert res3.status_code == 200

        # After 5 seconds we should have a new response
        assert res1.data != res3.data

    async def test_with_cache_content_type(self):
        # First Request
        res1 = await self.client.get('with-html-response-cache')
        assert res1.status_code == 200

        # Second Request
        res2 = await self.client.get('with-html-response-cache')
        assert res2.status_code == 200

        # Response should be cached
        assert res1.data == res2.data

        # Check Content-Type
        assert res1.headers['Content-Type'] == res2.headers['Content-Type']
