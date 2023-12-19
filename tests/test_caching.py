import time
from datetime import timedelta
from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.test import APIClient


@API()
def without_cache_api():
    return {'detail': time.time()}


@API()
def without_cache_api():
    return {'detail': time.time()}


@API(cache=True)
def with_cache_api():
    return {'detail': time.time()}


@API(cache=True, cache_exp_time=timedelta(seconds=5))
def expired_cache_api():
    return {'detail': time.time()}


urls = {
    'without-cache': without_cache_api,
    'with-cache': with_cache_api,
    'with-expired-cache': expired_cache_api,
}


class TestCaching(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def test_without_cache(self):
        res1 = self.client.get('without-cache')
        assert res1.status_code == 200

        res2 = self.client.get('without-cache')
        assert res2.status_code == 200

        assert res1.data != res2.data

    def test_with_cache(self):
        res1 = self.client.get('with-cache')
        assert res1.status_code == 200

        res2 = self.client.get('with-cache')
        assert res2.status_code == 200

        assert res1.data == res2.data

    def test_with_cache_5second_exp_time(self):
        # First Request
        with self.assertLogs(level='INFO') as captured:
            res1 = self.client.get('with-expired-cache')
        assert res1.status_code == 200

        # Check Logs
        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == '"cache_exp_time" is not very accurate when redis is not connected.'

        # Second Request
        res2 = self.client.get('with-expired-cache')
        assert res2.status_code == 200

        # Response should be cached
        assert res1.data == res2.data

        time.sleep(5)

        # Third Request
        res3 = self.client.get('with-expired-cache')
        assert res3.status_code == 200

        # After 5 seconds we should have a new response
        assert res1.data != res3.data

