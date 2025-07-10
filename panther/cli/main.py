import logging
import sys

from panther import version as panther_version
from panther.cli.create_project_command import create
from panther.cli.create_user_command import create_user
from panther.cli.monitor_command import monitor
from panther.cli.run_command import run
from panther.cli.utils import cli_error, print_help_message

logger = logging.getLogger('panther')


def shell(args) -> None:
    if len(args) == 0:
        return cli_error(
            'Not Enough Arguments, Give me a file path that contains `Panther()` app.\n'
            '       * Make sure to run `panther shell` in the same directory as that file!\n'
            '       * Example: `panther shell main.py`',
        )
    elif len(args) != 1:
        return cli_error('Too Many Arguments.')

    package = args[0].removesuffix('.py')
    try:
        from IPython import start_ipython

        start_ipython(('--gui', 'asyncio', '-c', f'"import {package}"', '-i'))
    except ImportError:
        logger.error('Make sure `ipython` is installed -> Hint: `pip install ipython`')


def version() -> None:
    print(panther_version())


def start() -> None:
    args = sys.argv[2:]
    match len(sys.argv) > 1 and sys.argv[1]:
        case 'h' | 'help' | '-h' | '--help':
            print_help_message()
        case 'create':
            create(args)
        case 'createuser':
            create_user(args)
        case 'run':
            run(args)
        case 'shell':
            shell(args)
        case 'monitor':
            monitor()
        case 'version' | '--version':
            version()
        case _:
            cli_error('Invalid Arguments.')
