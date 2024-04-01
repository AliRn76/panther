import contextlib
import os

import uvicorn

from panther.cli.utils import print_uvicorn_help_message, clean_args, cli_error


def _handle_commands(args: dict[str, str | None]) -> dict:
    """
    Boolean Commands:
    - reload
    - access-log
    - no-access-log
    - use-colors
    - no-use-colors
    - server-header
    - no-server-header

    Int Commands:
    - port
    - ws_max_size
    - ws_max_queue
    - ws_ping_interval
    - ws_ping_timeout
    """
    _command = {}

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

    if 'port' in args:
        _command['port'] = int(args.pop('port'))

    if 'ws_max_size' in args:
        _command['ws_max_size'] = int(args.pop('ws_max_size'))

    if 'ws_max_queue' in args:
        _command['ws_max_queue'] = int(args.pop('ws_max_queue'))

    if 'ws_ping_interval' in args:
        _command['ws_ping_interval'] = int(args.pop('ws_ping_interval'))

    if 'ws_ping_timeout' in args:
        _command['ws_ping_timeout'] = int(args.pop('ws_ping_timeout'))

    return _command


def run(args: list[str]) -> None:
    args = clean_args(args)

    if any(a in args for a in ['h', 'help', '-h', '--help']):
        print_uvicorn_help_message()
        return
    command = {'app_dir': os.getcwd()}
    command.update(_handle_commands(args))
    command.update(args)
    try:
        with contextlib.suppress(KeyboardInterrupt):
            uvicorn.run('main:app', **command)
    except TypeError as e:
        cli_error(e)
