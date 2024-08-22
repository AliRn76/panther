import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from panther import Panther
from panther.configs import config
from panther.middlewares import BaseMiddleware
from panther.utils import generate_secret_key, generate_hash_value_from_string, load_env, round_datetime


class TestLoadEnvFile(TestCase):
    file_path = 'tests/env-test'

    is_active = True
    db_host = '127.0.0.1'
    db_port = 27017

    def tearDown(self) -> None:
        Path(self.file_path).unlink(missing_ok=True)

    def _create_env_file(self, file_data):
        with open(self.file_path, 'w') as file:
            file.write(file_data)

    def test_load_env_invalid_file(self):
        try:
            load_env('fake.file')
        except ValueError as e:
            assert e.args[0] == '"fake.file" is not a file.'

    def test_load_env_double_quote(self):
        self._create_env_file(f"""
IS_ACTIVE = "{self.is_active}"
DB_HOST = "{self.db_host}"
DB_PORT = "{self.db_port}"
        """)

        variables = load_env(self.file_path)
        assert (variables['IS_ACTIVE'] == 'True') == self.is_active
        assert variables['DB_HOST'] == self.db_host
        assert variables['DB_PORT'] == str(self.db_port)

    def test_load_env_single_quote(self):
        self._create_env_file(f"""
IS_ACTIVE = '{self.is_active}'
DB_HOST = '{self.db_host}'
DB_PORT = '{self.db_port}'
                """)

        variables = load_env(self.file_path)
        assert (variables['IS_ACTIVE'] == 'True') == self.is_active
        assert variables['DB_HOST'] == self.db_host
        assert variables['DB_PORT'] == str(self.db_port)

    def test_load_env_no_quote(self):
        self._create_env_file(f"""
IS_ACTIVE = {self.is_active}
DB_HOST = {self.db_host}
DB_PORT = {self.db_port}

                    """)

        variables = load_env(self.file_path)
        assert (variables['IS_ACTIVE'] == 'True') == self.is_active
        assert variables['DB_HOST'] == self.db_host
        assert variables['DB_PORT'] == str(self.db_port)

    def test_load_env_no_space(self):
        self._create_env_file(f"""
IS_ACTIVE={self.is_active}
DB_HOST={self.db_host}
DB_PORT={self.db_port}
                    """)

        variables = load_env(self.file_path)
        assert (variables['IS_ACTIVE'] == 'True') == self.is_active
        assert variables['DB_HOST'] == self.db_host
        assert variables['DB_PORT'] == str(self.db_port)

    def test_load_env_not_striped(self):
        self._create_env_file(f"""
        IS_ACTIVE = {self.is_active}
        DB_HOST = {self.db_host}
        DB_PORT = {self.db_port}
                    """)

        variables = load_env(self.file_path)
        assert (variables['IS_ACTIVE'] == 'True') == self.is_active
        assert variables['DB_HOST'] == self.db_host
        assert variables['DB_PORT'] == str(self.db_port)

    def test_load_env_and_read_from_system_env(self):
        self._create_env_file(f"""
IS_ACTIVE = '{self.is_active}'
DB_HOST = '{self.db_host}'
DB_PORT = '{self.db_port}'
                """)

        load_env(self.file_path)
        assert (os.environ['IS_ACTIVE'] == 'True') == self.is_active
        assert os.environ['DB_HOST'] == self.db_host
        assert os.environ['DB_PORT'] == str(self.db_port)


class TestUtilFunctions(TestCase):

    def test_round_datetime_second_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(seconds=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=40)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_second_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=35)
        _delta = timedelta(seconds=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=40)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_minute_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=15, second=30)
        _delta = timedelta(minutes=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=20)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_minute_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(minutes=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=20)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_hour_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(hours=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_hour_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=10, minute=10, second=30)
        _delta = timedelta(hours=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_day_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=10, minute=10, second=30)
        _delta = timedelta(days=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=23)
        assert rounded_datetime == expected_datetime

    def test_round_datetime_day_2(self):
        _datetime = datetime(year=1997, month=12, day=22, hour=10, minute=10, second=30)
        _delta = timedelta(days=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=23)
        assert rounded_datetime == expected_datetime

    def test_generate_hash_value_from_string(self):
        text = 'Hello World'
        hashed_1 = generate_hash_value_from_string(text)
        hashed_2 = generate_hash_value_from_string(text)

        assert hashed_1 == hashed_2
        assert text != hashed_1


class TestLoadConfigs(TestCase):
    def setUp(self):
        config.refresh()

    def test_urls_not_found(self):
        global URLs
        URLs = None

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__)
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'URLs': required."

    def test_urls_cant_be_dict(self):
        global URLs
        URLs = {}

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__)
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        msg = (
            "Invalid 'URLs': can't be 'dict', you may want to pass it's value directly to Panther(). "
            "Example: Panther(..., urls=...)"
        )
        assert captured.records[0].getMessage() == msg

    def test_urls_not_string(self):
        global URLs
        URLs = True

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__)
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'URLs': should be dotted string."

    def test_urls_invalid_target(self):
        global URLs
        URLs = 'tests.test_utils.TestLoadConfigs'

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__)
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'URLs': should point to a dict."

    def test_urls_invalid_module_path(self):
        global URLs
        URLs = 'fake.module'

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__)
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'URLs': No module named 'fake'"

    def test_middlewares_invalid_path(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            ('fake.module', {})
        ]

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                MIDDLEWARES = []

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'MIDDLEWARES': fake.module is not a valid middleware path"

    def test_middlewares_invalid_structure(self):
        global MIDDLEWARES
        MIDDLEWARES = ['fake.module']

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                MIDDLEWARES = []

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'MIDDLEWARES': fake.module should have 2 part: (path, kwargs)"

    def test_middlewares_too_many_args(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            ('fake.module', 1, 2)
        ]

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                MIDDLEWARES = []

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'MIDDLEWARES': ('fake.module', 1, 2) too many arguments"

    def test_middlewares_without_args(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            ('tests.test_utils.CorrectTestMiddleware', )
        ]

        with self.assertNoLogs(level='ERROR'):
            Panther(name=__name__, configs=__name__, urls={})

        MIDDLEWARES = []

    def test_middlewares_invalid_middleware_parent(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            ('tests.test_utils.TestMiddleware', )
        ]

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                MIDDLEWARES = []

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'MIDDLEWARES': is not a sub class of BaseMiddleware"

    def test_jwt_auth_without_secret_key(self):
        global AUTHENTICATION
        AUTHENTICATION = 'panther.authentications.JWTAuthentication'

        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                AUTHENTICATION = None

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == "Invalid 'JWTConfig': `JWTConfig.key` or `SECRET_KEY` is required."

    def test_jwt_auth_with_secret_key(self):
        global AUTHENTICATION, SECRET_KEY
        AUTHENTICATION = 'panther.authentications.JWTAuthentication'
        SECRET_KEY = generate_secret_key()

        with self.assertNoLogs(level='ERROR'):
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert False
            else:
                assert True
            finally:
                AUTHENTICATION = None
                SECRET_KEY = None

    def test_check_function_endpoint_decorator(self):
        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={'/': invalid_api})
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'You may have forgotten to use `@API()` on the `tests.test_utils.invalid_api()`'

    def test_check_class_endpoint_inheritance(self):
        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={'/': InvalidAPI})
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == (
            f'You may have forgotten to inherit from `panther.app.GenericAPI` or `panther.app.GenericWebsocket` '
            f'on the `tests.test_utils.InvalidAPI()`'
        )

    def test_check_websocket_inheritance(self):
        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={'/': InvalidWebsocket})
            except SystemExit:
                assert True
            else:
                assert False

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == (
            f'You may have forgotten to inherit from `panther.app.GenericAPI` or `panther.app.GenericWebsocket` '
            f'on the `tests.test_utils.InvalidWebsocket()`'
        )


def invalid_api():
    pass


class InvalidAPI:
    pass


class InvalidWebsocket:
    pass


class CorrectTestMiddleware(BaseMiddleware):
    pass


class TestMiddleware:
    pass
