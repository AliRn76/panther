import sys
import time
from pathlib import Path
from typing import NoReturn

from panther.cli.template import Template
from panther.cli.utils import cli_error


def create(args: list) -> NoReturn:
    # Get Project Name
    if len(args) == 0:
        return cli_error('Not Enough Parameters.')
    project_name = args[0]

    # Get Base Directory
    base_directory: str = '.'
    if len(args) > 1:
        base_directory = args[1]

    # Check All The Directories Existence
    existence = check_all_directories(base_directory)
    if existence:
        return cli_error(f'"{existence}" Directory Already Exists.')

    load_animation()

    # Create Base Directory
    if base_directory != '.':
        Path(base_directory).mkdir()

    for file_name, data in Template.items():
        if isinstance(data, dict):
            # Create Sub Directory
            sub_directory = f'{base_directory}/{file_name}'
            Path(sub_directory).mkdir()

            # Create Files of Sub Directory
            for sub_file_name, sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                sub_data = sub_data.replace('{PROJECT_NAME}', project_name.lower())
                with open(file_path, 'x') as file:
                    file.write(sub_data)
        else:
            # Create File
            data = data.replace('{PROJECT_NAME}', project_name.lower())
            file_path = f'{base_directory}/{file_name}'
            with open(file_path, 'x') as file:
                file.write(data)

    print('Project Created Successfully.')


def check_all_directories(base_directory: str) -> str | None:
    """Return folder_name means that the directory exist."""
    if base_directory != '.' and Path(base_directory).is_dir():
        return base_directory

    for file_name, data in Template.items():
        sub_directory = f'{base_directory}/{file_name}'
        if Path(sub_directory).exists():
            return sub_directory

        if isinstance(data, dict):
            for sub_file_name in data:
                file_path = f'{sub_directory}/{sub_file_name}'
                if Path(file_path).exists():
                    return file_path


def load_animation() -> NoReturn:
    animation = [
        '■□□□□□□□□□□',
        '■■□□□□□□□□□',
        '■■■□□□□□□□□',
        '■■■■□□□□□□□',
        '■■■■■□□□□□□',
        '■■■■■■□□□□□',
        '■■■■■■■□□□□',
        '■■■■■■■■□□□',
        '■■■■■■■■■□□',
        '■■■■■■■■■■□',
        '■■■■■■■■■■■',
    ]

    for i in range(len(animation)):
        time.sleep(0.2)
        sys.stdout.write('\r' + 'Creating Your Project: ' + animation[i % len(animation)])
        sys.stdout.flush()

    print('\n')
