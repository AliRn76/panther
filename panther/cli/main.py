import os
import sys

from rich import print as rprint

from panther import version as panther_version
from panther.cli.create_command import create
from panther.cli.monitor_command import monitor
from panther.cli.run_command import run
from panther.cli.utils import clean_args, cli_error, help_message


def shell() -> None:
    os.system('bpython')


def version() -> None:
    print(panther_version())


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
        case 'version':
            version()
        case _:
            cli_error('Invalid Arguments.')
