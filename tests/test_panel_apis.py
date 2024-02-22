from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.test import APIClient

DB_PATH = 'test.pdb'
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': DB_PATH,
    },
}


class TestPanelAPIs(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls={})
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        Path(DB_PATH).unlink()

    async def test_list_of_models(self):
        response = await self.client.get('_panel')
        expected_keys = ['name', 'module', 'index']
        assert expected_keys == [*response.data[0].keys()]
