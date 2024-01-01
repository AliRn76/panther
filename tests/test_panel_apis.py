from pathlib import Path
from unittest import TestCase

from panther import Panther
from panther.test import APIClient

DB_PATH = 'test.pdb'
MIDDLEWARES = [
    ('panther.middlewares.db.DatabaseMiddleware', {'url': f'pantherdb://{DB_PATH}'}),
]


class TestPanelAPIs(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls={})
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        Path(DB_PATH).unlink()

    def test_list_of_models(self):
        response = self.client.get('_panel')
        expected_keys = ['name', 'module', 'index']
        assert expected_keys == [*response.data[0].keys()]
