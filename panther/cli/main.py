import os
import sys
from pathlib import Path
from subprocess import Popen
from watchfiles import watch
from rich import print as rprint
from panther.cli.template import Template

logo = r"""│    ____                 __    __                         │
│   /\  _`\              /\ \__/\ \                        │
│   \ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __     │
│    \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\   │
│     \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/    │
│      \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\    │
│       \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/    │
"""

help_message = f"""╭{58*'─'}╮
{logo}│{58*' '}│
│                                                          │
│   usage:                                                 │
│       - panther create <project_name>                    │
│           Create your project in current directory       │
│                                                          │
│       - panther run [--reload]                           │
│           Run your project with uvicorn                  │
│                                                          │
│       - panther shell                                    │
│           Run interactive python shell                   │
│                                                          │
│       - panther monitor                                  │
│           Show the monitor :)                            │
│                                                          │
│       - panther [--help | -h | help]                     │
│           Show this message and exit                     │
╰{58*'─'}╯
"""


def error(message: str) -> None:
    print(f'Error: {message}\n\nuse panther -h for more help')


def create(args: list):
    base_dir = Path(__name__).resolve().parent

    if len(args) == 0:
        return error('Not Enough Parameters.')
    project_name = args[0]

    # TODO: Add Custom BaseDirectory

    if os.path.isdir(project_name):
        return error(f'"{project_name}" Directory Already Exists.')
    os.makedirs(project_name)

    for file_name, data in Template.items():
        if isinstance(data, dict):
            sub_directory = f'{project_name}/{file_name}'
            os.makedirs(sub_directory)
            for sub_file_name, sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                with open(file_path, 'x') as file:
                    file.write(sub_data)
        else:
            if file_name == 'alembic.ini':
                data = data.replace('{SQLALCHEMY_URL}', f'sqlite:///{base_dir}/{project_name}/{project_name.lower()}.db')
            elif file_name == '.env':
                data = data.replace('{DATABASE_NAME}', project_name.lower())

            file_path = f'{project_name}/{file_name}'
            with open(file_path, 'x') as file:
                file.write(data)


def run(args) -> None:
    command = ['uvicorn', 'main:app', '--no-access-log']
    command.extend(args)
    sp = Popen(command)
    try:
        sp.wait()
    except KeyboardInterrupt:
        sp.kill()


def shell() -> None:
    os.system('bpython')


def start() -> None:
    if len(sys.argv) == 1 or sys.argv[1] in ['help', '-h', '--help']:
        rprint(help_message)
        return

    if sys.argv[1] == 'create':
        create(sys.argv[2:])
        print('Project Created Successfully.')
    elif sys.argv[1] == 'run':
        run(sys.argv[2:])
    elif sys.argv[1] == 'shell':
        shell()
    elif sys.argv[1] == 'monitor':
        # TODO: Is it only watch logs/monitoring.log or the whole directory ?
        with open('logs/monitoring.log', 'r') as f:
            f.readlines()
            for _ in watch('logs/monitoring.log'):
                print(f.readline())
    else:
        error('Invalid Arguments.')
