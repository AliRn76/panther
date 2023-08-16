from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from panther.utils import generate_hash_value_from_string, load_env, round_datetime


class TestLoadEnvFile(TestCase):
    file_path = 'tests/env-test'

    secret_key = 'SecretKey'
    db_name = 'panther'
    db_host = '127.0.0.1'
    db_port = 27017
    db_username = 'Username'
    db_password = 'Password'

    def tearDown(self) -> None:
        Path(self.file_path).unlink()

    def create_env_file(self, file_data):
        with open(self.file_path, 'w') as file:
            file.write(file_data)

    def test_load_env_double_quote(self):
        self.create_env_file(f"""
SECRET_KEY = "{self.secret_key}"

DB_NAME = "{self.db_name}"
DB_HOST = "{self.db_host}"
DB_PORT = "{self.db_port}"
DB_USERNAME = "{self.db_username}"
DB_PASSWORD = "{self.db_password}"
        """)
        variables = load_env(self.file_path)
        self.assertEqual(variables['SECRET_KEY'], self.secret_key)
        self.assertEqual(variables['DB_NAME'], self.db_name)
        self.assertEqual(variables['DB_HOST'], self.db_host)
        self.assertEqual(variables['DB_PORT'], str(self.db_port))
        self.assertEqual(variables['DB_USERNAME'], self.db_username)
        self.assertEqual(variables['DB_PASSWORD'], self.db_password)

    def test_load_env_single_quote(self):
        self.create_env_file(f"""
SECRET_KEY = '{self.secret_key}'

DB_NAME = '{self.db_name}'
DB_HOST = '{self.db_host}'
DB_PORT = '{self.db_port}'
DB_USERNAME = '{self.db_username}'
DB_PASSWORD = '{self.db_password}'
                """)

        variables = load_env(self.file_path)
        self.assertEqual(variables['SECRET_KEY'], self.secret_key)
        self.assertEqual(variables['DB_NAME'], self.db_name)
        self.assertEqual(variables['DB_HOST'], self.db_host)
        self.assertEqual(variables['DB_PORT'], str(self.db_port))
        self.assertEqual(variables['DB_USERNAME'], self.db_username)
        self.assertEqual(variables['DB_PASSWORD'], self.db_password)

    def test_load_env_no_quote(self):
        self.create_env_file(f"""
SECRET_KEY = {self.secret_key}

DB_NAME = {self.db_name}
DB_HOST = {self.db_host}
DB_PORT = {self.db_port}
DB_USERNAME = {self.db_username}
DB_PASSWORD = {self.db_password}
                    """)

        variables = load_env(self.file_path)
        self.assertEqual(variables['SECRET_KEY'], self.secret_key)
        self.assertEqual(variables['DB_NAME'], self.db_name)
        self.assertEqual(variables['DB_HOST'], self.db_host)
        self.assertEqual(variables['DB_PORT'], str(self.db_port))
        self.assertEqual(variables['DB_USERNAME'], self.db_username)
        self.assertEqual(variables['DB_PASSWORD'], self.db_password)

    def test_load_env_no_space(self):
        self.create_env_file(f"""
SECRET_KEY={self.secret_key}

DB_NAME={self.db_name}
DB_HOST={self.db_host}
DB_PORT={self.db_port}
DB_USERNAME={self.db_username}
DB_PASSWORD={self.db_password}
                    """)

        variables = load_env(self.file_path)
        self.assertEqual(variables['SECRET_KEY'], self.secret_key)
        self.assertEqual(variables['DB_NAME'], self.db_name)
        self.assertEqual(variables['DB_HOST'], self.db_host)
        self.assertEqual(variables['DB_PORT'], str(self.db_port))
        self.assertEqual(variables['DB_USERNAME'], self.db_username)
        self.assertEqual(variables['DB_PASSWORD'], self.db_password)

    def test_load_env_not_striped(self):
        self.create_env_file(f"""
        SECRET_KEY = {self.secret_key}

        DB_NAME = {self.db_name}
        DB_HOST = {self.db_host}
        DB_PORT = {self.db_port}
        DB_USERNAME={self.db_username}
        DB_PASSWORD = {self.db_password}
                    """)

        variables = load_env(self.file_path)
        self.assertEqual(variables['SECRET_KEY'], self.secret_key)
        self.assertEqual(variables['DB_NAME'], self.db_name)
        self.assertEqual(variables['DB_HOST'], self.db_host)
        self.assertEqual(variables['DB_PORT'], str(self.db_port))
        self.assertEqual(variables['DB_USERNAME'], self.db_username)
        self.assertEqual(variables['DB_PASSWORD'], self.db_password)


class TestUtilFunctions(TestCase):

    def test_round_datetime_second_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(seconds=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=40)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_second_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=35)
        _delta = timedelta(seconds=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=40)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_minute_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=15, second=30)
        _delta = timedelta(minutes=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=20)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_minute_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(minutes=20)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12, minute=20)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_hour_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=12, minute=10, second=30)
        _delta = timedelta(hours=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_hour_2(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=10, minute=10, second=30)
        _delta = timedelta(hours=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=25, hour=12)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_day_1(self):
        _datetime = datetime(year=1997, month=12, day=25, hour=10, minute=10, second=30)
        _delta = timedelta(days=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=23)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_round_datetime_day_2(self):
        _datetime = datetime(year=1997, month=12, day=22, hour=10, minute=10, second=30)
        _delta = timedelta(days=5)
        rounded_datetime = round_datetime(_datetime, _delta)

        expected_datetime = datetime(year=1997, month=12, day=23)
        self.assertEqual(rounded_datetime, expected_datetime)

    def test_generate_hash_value_from_string(self):
        text = 'Hello World'
        hashed_1 = generate_hash_value_from_string(text)
        hashed_2 = generate_hash_value_from_string(text)

        self.assertEqual(hashed_1, hashed_2)
        self.assertNotEqual(text, hashed_1)
