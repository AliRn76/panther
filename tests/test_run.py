import sys
from datetime import timedelta
from pathlib import Path
from unittest import TestCase

import tests.sample_project.app.models
from panther import Panther


class TestRun(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/sample_project')

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

    def test_init(self):
        app = Panther(__name__)
        self.assertIsInstance(app, Panther)

    def test_load_configs(self):
        from panther.configs import config
        from panther.panel.apis import documents_api, models_api, single_document_api

        base_dir = Path(__name__).resolve().parent
        secret_key = 'fHrIYx3yK0J_UG0K0zD6miLPNy1esoYXzVsvif6e7rY='
        Panther(__name__)

        assert isinstance(config, dict)
        assert config['base_dir'] == base_dir
        assert config['monitoring'] is True
        assert config['log_queries'] is True
        assert config['default_cache_exp'] == timedelta(seconds=10)
        assert config['throttling'].rate == 10
        assert config['throttling'].duration == timedelta(seconds=10)
        assert config['secret_key'] == secret_key.encode()

        assert len(config['http_middlewares']) == 1
        assert config['http_middlewares'][0].__class__.__name__ == 'DatabaseMiddleware'
        assert config['http_middlewares'][0].url == 'pantherdb://test.pdb'

        assert len(config['reversed_http_middlewares']) == 1
        assert config['reversed_http_middlewares'][0].__class__.__name__ == 'DatabaseMiddleware'
        assert config['reversed_http_middlewares'][0].url == 'pantherdb://test.pdb'

        assert len(config['ws_middlewares']) == 1
        assert config['ws_middlewares'][0].__class__.__name__ == 'DatabaseMiddleware'
        assert config['ws_middlewares'][0].url == 'pantherdb://test.pdb'

        assert len(config['reversed_ws_middlewares']) == 1
        assert config['reversed_ws_middlewares'][0].__class__.__name__ == 'DatabaseMiddleware'
        assert config['reversed_ws_middlewares'][0].url == 'pantherdb://test.pdb'

        assert config['user_model'].__name__ == tests.sample_project.app.models.User.__name__
        assert config['user_model'].__module__.endswith('app.models')
        assert config['jwt_config'].algorithm == 'HS256'
        assert config['jwt_config'].life_time == timedelta(days=2).total_seconds()
        assert config['jwt_config'].key == secret_key

        assert '' in config['urls']
        config['urls'].pop('')

        assert 'second' in config['urls']
        config['urls'].pop('second')

        urls = {
            '_panel': {
                '': models_api,
                '<index>': {
                    '': documents_api,
                    '<document_id>': single_document_api,
                },
            },
        }
        assert config['urls'] == urls
        assert config['db_engine'] == 'pantherdb'
