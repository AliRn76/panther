import os
import uvicorn
from rich import print as rprint
from panther.cli.utils import cli_error, run_help_message


def _handle_boolean_commands(args: dict[str, str | None]) -> dict:
    """Boolean Commands:
    - reload
    - access-log
    - no-access-log
    - use-colors
    - no-use-colors
    - server-header
    - no-server-header
    """
    _command = dict()

    if 'reload' in args:
        _command['reload'] = bool(args.pop('reload', None))

    _command['access_log'] = False  # Default
    if 'access-log' in args:
        _command['access_log'] = bool(args.pop('access-log', None))

    if 'no-access-log' in args:
        _command['access_log'] = not bool(args.pop('no-access-log', None))

    if 'use-colors' in args:
        _command['use_colors'] = bool(args.pop('use-colors', None))

    if 'no-use-colors' in args:
        _command['use_colors'] = not bool(args.pop('no-use-colors', None))

    if 'server-header' in args:
        _command['server_header'] = bool(args.pop('server-header', None))

    if 'no-server-header' in args:
        _command['server_header'] = not bool(args.pop('no-server-header', None))

    return _command


def run(args: dict[str, str | None]) -> None:
    if 'h' in args or 'help' in args:
        rprint(run_help_message)
        return
    command = {'app_dir': os.getcwd()}
    command.update(_handle_boolean_commands(args))
    command.update(args)

    try:
        uvicorn.run('main:app', **command)
    except TypeError as e:
        cli_error(e)
