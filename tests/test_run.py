import sys
from datetime import timedelta
from pathlib import Path
from unittest import TestCase

import tests.sample_project.app.models
from panther import Panther
from panther.configs import Config


class TestRun(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/sample_project')

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

    def test_init(self):
        app = Panther(__name__)
        assert isinstance(app, Panther)

    def test_load_configs(self):
        from panther.configs import config
        from panther.panel.apis import documents_api, models_api, single_document_api, healthcheck_api

        base_dir = Path(__name__).resolve().parent
        secret_key = 'fHrIYx3yK0J_UG0K0zD6miLPNy1esoYXzVsvif6e7rY='
        Panther(__name__)

        assert isinstance(config, Config)
        assert config.BASE_DIR == base_dir
        assert config.MONITORING is True
        assert config.LOG_QUERIES is True
        assert config.DEFAULT_CACHE_EXP == timedelta(seconds=10)
        assert config.THROTTLING.rate == 10
        assert config.THROTTLING.duration == timedelta(seconds=10)
        assert config.SECRET_KEY == secret_key.encode()

        assert len(config.HTTP_MIDDLEWARES) == 0
        assert len(config.WS_MIDDLEWARES) == 0

        assert config.USER_MODEL.__name__ == tests.sample_project.app.models.User.__name__
        assert config.USER_MODEL.__module__.endswith('app.models')
        assert config.JWT_CONFIG.algorithm == 'HS256'
        assert config.JWT_CONFIG.life_time == timedelta(days=2).total_seconds()
        assert config.JWT_CONFIG.key == secret_key

        assert '' in config.URLS
        config.URLS.pop('')

        assert 'second' in config.URLS
        config.URLS.pop('second')

        urls = {
            '_panel': {
                '': models_api,
                '<index>': {
                    '': documents_api,
                    '<document_id>': single_document_api,
                },
                'health': healthcheck_api
            },
        }
        assert config.URLS == urls
        assert config.QUERY_ENGINE.__name__ == 'BasePantherDBQuery'
