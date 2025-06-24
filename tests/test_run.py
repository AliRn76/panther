import sys
from datetime import timedelta
from pathlib import Path
from unittest import TestCase

import tests.sample_project.app.models
from panther import Panther
from panther.configs import Config, config


class TestRun(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/sample_project')

    @classmethod
    def tearDownClass(cls) -> None:
        config.refresh()
        sys.path.pop()

    def test_init(self):
        app = Panther(__name__)
        assert isinstance(app, Panther)

    def test_load_configs(self):
        from panther.panel.apis import documents_api, healthcheck_api, models_api, single_document_api

        base_dir = Path(__name__).resolve().parent
        secret_key = 'fHrIYx3yK0J_UG0K0zD6miLPNy1esoYXzVsvif6e7rY='
        Panther(__name__)

        assert isinstance(config, Config)
        assert base_dir == config.BASE_DIR
        assert config.LOG_QUERIES is True
        assert config.THROTTLING.rate == 10
        assert config.THROTTLING.duration == timedelta(seconds=10)
        assert secret_key == config.SECRET_KEY

        assert len(config.HTTP_MIDDLEWARES) == 1
        assert len(config.WS_MIDDLEWARES) == 0

        assert config.USER_MODEL.__name__ == tests.sample_project.app.models.User.__name__
        assert config.USER_MODEL.__module__.endswith('app.models')
        assert config.JWT_CONFIG.algorithm == 'HS256'
        assert config.JWT_CONFIG.life_time == int(timedelta(days=2).total_seconds())
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
                'health': healthcheck_api,
            },
        }
        # TODO: Fix this line, at the end of this task
        # assert config.URLS == urls
        assert config.QUERY_ENGINE.__name__ == 'BasePantherDBQuery'
