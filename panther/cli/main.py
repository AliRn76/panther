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

help_message = f"""╭{58 * '─'}╮
{logo}│{58 * ' '}│
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
╰{58 * '─'}╯
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
            if file_name == '.env':
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


def monitor() -> None:
    # TODO: Is it only watch logs/monitoring.log or the whole directory ?
    try:
        from rich import box
        from rich.table import Table
        from rich.live import Live
        from rich.layout import Layout
        from datetime import datetime

        from rich import box
        from rich.align import Align
        from rich.console import Console, Group
        from rich.layout import Layout
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
        from rich.syntax import Syntax
        from rich.table import Table
        from rich.text import Text

        table = Table(box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column('Datetime', justify='right', style='magenta', no_wrap=True)
        table.add_column('Message', style='cyan')
        table.add_column('Response Time', justify='right', style='blue')

        with open('logs/monitoring.log', 'r') as f:
            f.readlines()

            layout = Layout(name='root')
            layout['root'].update(
                Panel(
                    Align.center(Group(table)),
                    box=box.ROUNDED,
                    padding=(1, 2),
                    title='Monitoring',
                    border_style='bright_blue',
                )
            )

            with Live(layout, auto_refresh=False, vertical_overflow='visible', screen=True) as live:
                for _ in watch('logs/monitoring.log'):
                    data = f.readline().split('|')
                    table.add_row(*data)
                    live.update(layout)
                    live.refresh()

    except FileNotFoundError:
        error("Monitor Log File Does Not Exists.\n\nHint: Make sure 'Monitor' is True in 'core/configs' "
              "or you are in a correct directory.")
    except KeyboardInterrupt:
        pass


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
        monitor()

    else:
        error('Invalid Arguments.')
