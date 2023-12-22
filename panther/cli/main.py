import os
import sys

from panther import version as panther_version
from panther.cli.create_command import create
from panther.cli.monitor_command import monitor
from panther.cli.run_command import run
from panther.cli.utils import cli_error, cli_info, cli_warning, print_help_message


def shell(args: list) -> None:
    if len(args) == 0:
        cli_info('You may want to use "bpython" or "ipython" for better interactive shell')
        os.system('python')
    elif len(args) != 1:
        return cli_error('Too Many Arguments.')
    shell_type = args[0].lower()
    if shell_type not in ['ipython', 'bpython']:
        return cli_error(f'"{shell_type}" Is Not Supported.')

    # Bpython
    if shell_type == 'bpython':
        try:
            import bpython
            os.system('bpython')
        except ImportError as e:
            cli_warning(e, 'Hint: "pip install bpython"')
            os.system('python')

    # Ipython
    elif shell_type == 'ipython':
        try:
            import IPython
            os.system('ipython')
        except ImportError as e:
            cli_warning(e, 'Hint: "pip install ipython"')
            os.system('python')


def version() -> None:
    print(panther_version())


def start() -> None:
    args = sys.argv[2:]
    match len(sys.argv) > 1 and sys.argv[1]:
        case 'h' | 'help' | '-h' | '--help':
            print_help_message()
        case 'create':
            create(args)
        case 'run':
            run(args)
        case 'shell':
            shell(args)
        case 'monitor':
            monitor()
        case 'version':
            version()
        case _:
            cli_error('Invalid Arguments.')
