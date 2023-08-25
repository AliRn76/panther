import sys
from pathlib import Path
from unittest import TestCase

from panther import Panther


class TestRun(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/run')

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

    def test_init(self):
        app = Panther(__name__)
        self.assertIsInstance(app, Panther)

    def test_init_logs(self):
        base_dir = Path(__name__).resolve().parent
        with self.assertLogs(level='DEBUG') as captured:
            Panther(__name__)

            if sys.version_info.minor < 11:
                self.assertEqual(len(captured.records), 2)
                self.assertEqual(captured.records[0].getMessage(), 'Use Python Version 3.11+ For Better Performance.')
                self.assertEqual(captured.records[1].getMessage(), f'Base directory: {base_dir}')
            else:
                self.assertEqual(len(captured.records), 1)
                self.assertEqual(captured.records[0].getMessage(), f'Base directory: {base_dir}')

        if sys.version_info.minor < 11:
            with self.assertLogs(level='INFO') as captured:
                Panther(__name__)
                self.assertEqual(len(captured.records), 1)
                self.assertEqual(captured.records[0].getMessage(), 'Use Python Version 3.11+ For Better Performance.')
        else:
            with self.assertNoLogs(level='INFO'):
                Panther(__name__)

        if sys.version_info.minor < 11:
            with self.assertLogs(level='WARNING') as captured:
                Panther(__name__)
                self.assertEqual(len(captured.records), 1)
                self.assertEqual(captured.records[0].getMessage(), 'Use Python Version 3.11+ For Better Performance.')
        else:
            with self.assertNoLogs(level='INFO'):
                Panther(__name__)

        with self.assertNoLogs(level='ERROR'):
            Panther(__name__)

        with self.assertNoLogs(level='CRITICAL'):
            Panther(__name__)

    def test_load_configs(self):
        from panther.configs import config
        from panther.db.models import BaseUser
        from panther.panel.apis import documents_api, models_api, single_document_api

        base_dir = Path(__name__).resolve().parent
        app = Panther(__name__)

        self.assertIsInstance(app.configs, dict)
        self.assertEqual(app.configs.get('URLs'), 'core.configs.urls')

        self.assertIsInstance(config, dict)
        self.assertEqual(config['base_dir'], base_dir)
        self.assertFalse(config['monitoring'])
        self.assertFalse(config['log_queries'])
        self.assertFalse(config['default_cache_exp'])
        self.assertIsNone(config['throttling'])
        self.assertIsNone(config['secret_key'])
        self.assertEqual(config['middlewares'], [])
        self.assertEqual(config['reversed_middlewares'], [])
        self.assertEqual(config['user_model'], BaseUser)
        self.assertIsNone(config['jwt_config'])
        self.assertEqual(len(config['models']), 4)

        self.assertTrue('' in config['urls'])
        config['urls'].pop('')
        urls = {
            '_panel': {
                '': models_api,
                '<index>': {
                    '': documents_api,
                    '<document_id>': single_document_api,
                },
            },
        }
        self.assertEqual(config['urls'], urls)
        self.assertEqual(config['db_engine'], '')
