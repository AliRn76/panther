import os
import sys

from rich import print as rprint

from panther.cli.run_command import run
from panther.cli.create_command import create
from panther.cli.monitor_command import monitor
from panther.cli.utils import clean_args, help_message, cli_error


def shell() -> None:
    os.system('bpython')


def start() -> None:
    command = sys.argv and sys.argv[1] or None
    args = clean_args(sys.argv[2:])

    match command:
        case '-h' | '--help':
            rprint(help_message)
        case 'create':
            create(sys.argv[2:])
        case 'run':
            run(args)
        case 'shell':
            shell()
        case 'monitor':
            monitor()
        case _:
            cli_error('Invalid Arguments.')
