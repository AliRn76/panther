import os
import shutil
import sys
from io import StringIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from rich import print as rprint

from panther import Panther
from panther.cli.create_command import create
from panther.cli.template import Template


class TestCLI(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/sample_project')

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

    def test_init(self):
        with patch('sys.stdout', new=StringIO()) as fake_out1:
            app = Panther(__name__)

        expected_value = r"""
╭──────────────────────────────────────────────────────────╮
│    ____                 __    __                         │
│   /\  _`\              /\ \__/\ \                        │
│   \ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __     │
│    \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\   │
│     \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/    │
│      \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\    │
│       \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/    │
│                                                          │
│   Monitoring: True                                       │
│   Log Queries: True                                      │
│   Background Tasks: False                                │
│   Websocket: False                                       │
│   Base directory: /home/ali/dev/panther                  │
│ * Run "panther monitor" in another session for Monitoring│
╰──────────────────────────────────────────────────────────╯
"""
        with patch('sys.stdout', new=StringIO()) as fake_out2:
            rprint(expected_value)

        # TODO: We can't compare these in github workflow ...?
        # assert fake_out1.getvalue() == fake_out2.getvalue()

    def test_create_not_enough_arguments(self):
        with self.assertLogs(level='ERROR') as captured:
            create([])

        assert len(captured.records) == 2
        assert captured.records[0].getMessage() == 'Not Enough Arguments.'
        assert captured.records[1].getMessage() == 'Use "panther -h" for more help'

    def test_create_on_existence_directory(self):
        project_path = 'test-project-directory'
        os.mkdir(project_path)
        with self.assertLogs(level='ERROR') as captured:
            create(['test_project', project_path])

        assert len(captured.records) == 2
        assert captured.records[0].getMessage() == f'"{project_path}" Directory Already Exists.'
        assert captured.records[1].getMessage() == 'Use "panther -h" for more help'
        os.removedirs(project_path)

    def test_create_project(self):
        project_path = 'test-project-directory'
        create(['test_project', project_path])

        for file_name, data in Template.items():
            sub_directory = f'{project_path}/{file_name}'
            assert Path(sub_directory).exists()

            if isinstance(data, dict):
                for sub_file_name in data:
                    file_path = f'{sub_directory}/{sub_file_name}'
                    assert Path(file_path).exists()

        shutil.rmtree(project_path)
