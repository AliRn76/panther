import time
from pathlib import Path

from rich import print as rich_print
from rich.console import Console
from rich.progress import ProgressBar

from panther import version
from panther.cli.template import Template


# ERASE_LINE = 100 * ' '
ERASE_LINE = '\x1b[2K'

# REMOVE_LAST_LINE = f'\033[1A[{ERASE_LINE}'
REMOVE_LAST_LINE = f'\x1b[1A{ERASE_LINE}'

PROGRESS_LEN = 8
BAR = ProgressBar(total=PROGRESS_LEN, width=40)
console = Console()


def create(args: list) -> None:
    collected_data = _collect_creation_data()

    project_name = collected_data['Project Name']
    base_directory = collected_data['Directory']

    # Create Base Directory
    if base_directory != '.':
        Path(base_directory).mkdir()

    for file_name, data in Template.items():
        if isinstance(data, dict):
            # Create Sub Directory
            sub_directory = f'{base_directory}/{file_name}'
            Path(sub_directory).mkdir()

            # Create Files of Sub Directory
            for sub_file_name, _sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                sub_data = _sub_data.replace('{PROJECT_NAME}', project_name.lower())
                sub_data = _sub_data.replace('{PANTHER_VERSION}', version())
                with Path(file_path).open('x') as file:
                    file.write(sub_data)
        else:
            # Create File
            new_data = data.replace('{PROJECT_NAME}', project_name.lower())
            file_path = f'{base_directory}/{file_name}'
            with Path(file_path).open('x') as file:
                file.write(new_data)


def _collect_creation_data() -> dict:
    collected_data = {}
    _progress(0)

    # # # Project Name
    project_name = input('Project Name: ')
    while project_name == '':
        print(end=REMOVE_LAST_LINE, flush=True)
        console.print("Project Name Can't Be Empty.", style='bold red')
        project_name = input('Project Name: ')
        print(end=REMOVE_LAST_LINE, flush=True)
    collected_data['Project Name'] = project_name
    _progress(1)

    # # # Project Directory
    directory = input('Directory (default is .): ') or '.'
    while existence := _check_all_directories(directory):
        print(end=REMOVE_LAST_LINE, flush=True)
        console.print(f'"{existence}" Directory Already Exists.', style='bold red')
        directory = input('Directory (default is .): ') or '.'
        print(end=REMOVE_LAST_LINE, flush=True)
    collected_data['Directory'] = directory
    _progress(2)

    # # # Database
    database_msg = (
        '    0: PantherDB\n'
        '    1: MongoDB\n'
        '    2: No Database\n'
        'Choose Your Database (default is 0): '
    )
    database = input(database_msg) or '0'
    while database not in ['0', '1', '2']:
        [print(end=REMOVE_LAST_LINE, flush=True) for _ in range(4)]
        console.print('Invalid Choice [0, 1, 2]', style='bold red')
        database = input(database_msg) or '0'
        print(end=REMOVE_LAST_LINE, flush=True)
    collected_data['Database'] = database
    _progress(3, extra_rows=3)

    # # # Database Encryption
    if collected_data['Database'] == '0':
        encryption = input('Do You Want Encryption For Your Database (y/ n): ')
        while not _is_boolean(encryption):
            print(end=REMOVE_LAST_LINE, flush=True)
            console.print('Invalid Choice [y, n]', style='bold red')
            encryption = input('Do You Want Encryption For Your Database (y/ n): ')
            print(end=REMOVE_LAST_LINE, flush=True)
        collected_data['Database Encryption'] = encryption
    else:
        print(flush=True)
    _progress(4)

    # # # Authentication
    collected_data['Authentication'] = input('Do You Want To Use JWT Authentication (y/ n): ')
    _progress(5)

    # # # Monitoring
    collected_data['Monitoring'] = input('Do You Want To Use Built-in Monitoring (y/ n): ')
    _progress(6)

    # # # Log Queries
    collected_data['Log Queries'] = input('Do You Want To Log Queries (y/ n): ')
    _progress(7)

    # # # Auto Reformat
    collected_data['Auto Reformat'] = input('Do You Want To Uses Auto Reformat (y/ n): ')
    _progress(8)

    return collected_data


def _progress(step: int, /, extra_rows: int = 0):
    for i in range(extra_rows + 3 if step else 0):
        print(REMOVE_LAST_LINE, flush=True, end='\r')
        time.sleep(.06)

    BAR.update(step)

    message = 'Created Successfully' if step == PROGRESS_LEN else 'Creating Project'
    rich_print(f'[b]{message:<21}[/b]', end='', flush=True)
    rich_print(BAR, flush=True)
    print('\n', flush=True)


def _is_boolean(_input: str):
    return _input.lower() in ['y', 'n']


def _check_all_directories(base_directory: str) -> str | None:
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


_collect_creation_data()
