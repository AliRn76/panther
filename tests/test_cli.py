import os
import shutil
import sys
from io import StringIO
from pathlib import Path
from unittest import TestCase, skipIf
from unittest.mock import patch

from rich import print as rprint

from panther import Panther
from panther.cli.create_command import CreateProject
from panther.cli.template import TEMPLATE, SINGLE_FILE_TEMPLATE
from panther.configs import config

interactive_cli_1_index = 0
interactive_cli_2_index = 0


# 0.ProjectName, 1.BaseDir, 2.IsSingleFile, 3.Database,
# 4.Encryption, 5.Authentication, 6.Monitoring, 7.LogQueries, 8.AutoReformat
def interactive_cli_1_mock_responses(index=None):
    global interactive_cli_1_index
    if index is None:
        index = interactive_cli_1_index
    responses = ['project1', 'project1_dir', 'n', '0', 'y', 'n', 'y', 'y', 'y', 'y']
    response = responses[index]
    interactive_cli_1_index += 1
    return response


def interactive_cli_2_mock_responses(index=None):
    global interactive_cli_2_index
    if index is None:
        index = interactive_cli_2_index
    responses = ['project2', 'project2_dir', 'y', '0', 'y', 'n', 'y', 'y', 'y', 'y']
    response = responses[index]
    interactive_cli_2_index += 1
    return response


class TestCLI(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        config.refresh()
        sys.path.append('tests/sample_project')

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

    @skipIf(sys.platform.startswith('win'), 'Not supported in windows')
    def test_print_info(self):
        with patch('sys.stdout', new=StringIO()) as fake_out1:
            app = Panther(__name__)

        base_dir = '{0:<39}'.format(str(Path(__name__).absolute().parent))
        expected_value = fr"""╭──────────────────────────────────────────────────────────╮
│    ____                 __    __                         │
│   /\  _`\              /\ \__/\ \                        │
│   \ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __     │
│    \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\   │
│     \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/    │
│      \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\    │
│       \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/    │
│                                                          │
│   Redis: False                                           │
│   Websocket: False                                       │
│   Monitoring: True                                       │
│   Log Queries: True                                      │
│   Background Tasks: False                                │
│   Base directory: {base_dir}│
│ * Run "panther monitor" in another session for Monitoring│
│ * You may want to install `uvloop` for better performance│
│   `pip install uvloop`                                   │
╰──────────────────────────────────────────────────────────╯"""
        with patch('sys.stdout', new=StringIO()) as fake_out2:
            rprint(expected_value)
        assert fake_out1.getvalue() == fake_out2.getvalue()

    @patch('builtins.input', interactive_cli_1_mock_responses)
    def test_create_normal_template_with_interactive_cli(self):
        CreateProject().create([])

        project_path = interactive_cli_1_mock_responses(1)
        for file_name, data in SINGLE_FILE_TEMPLATE.items():
            sub_directory = f'{project_path}/{file_name}'
            assert Path(sub_directory).exists()

            if isinstance(data, dict):
                for sub_file_name in data:
                    file_path = f'{sub_directory}/{sub_file_name}'
                    assert Path(file_path).exists()
        shutil.rmtree(project_path)

    @patch('builtins.input', interactive_cli_2_mock_responses)
    def test_create_single_file_template_with_interactive_cli(self):
        CreateProject().create([])

        project_path = interactive_cli_2_mock_responses(1)
        for file_name, data in SINGLE_FILE_TEMPLATE.items():
            sub_directory = f'{project_path}/{file_name}'
            assert Path(sub_directory).exists()

            if isinstance(data, dict):
                for sub_file_name in data:
                    file_path = f'{sub_directory}/{sub_file_name}'
                    assert Path(file_path).exists()
        shutil.rmtree(project_path)

    def test_create_on_existence_directory(self):
        project_path = 'test-project-directory'
        os.mkdir(project_path)

        with self.assertLogs(level='ERROR') as captured_error:
            CreateProject().create(['test_project', project_path])

        with self.assertLogs(level='INFO') as captured_info:
            CreateProject().create(['test_project', project_path])

        try:
            assert len(captured_error.records) == 1
            assert captured_info.records[0].getMessage() == f'"{project_path}" Directory Already Exists.'

            assert len(captured_info.records) == 2
            assert captured_info.records[0].getMessage() == f'"{project_path}" Directory Already Exists.'
            assert captured_info.records[1].getMessage() == 'Use "panther -h" for more help'
        except AssertionError as e:
            raise e
        finally:
            os.removedirs(project_path)

    def test_create_project(self):
        project_path = 'test-project-directory'
        CreateProject().create(['test_project', project_path])

        for file_name, data in TEMPLATE.items():
            sub_directory = f'{project_path}/{file_name}'
            assert Path(sub_directory).exists()

            if isinstance(data, dict):
                for sub_file_name in data:
                    file_path = f'{sub_directory}/{sub_file_name}'
                    assert Path(file_path).exists()

        shutil.rmtree(project_path)
