import logging
from rich import print as rprint


logger = logging.getLogger('panther')


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
│       - panther create <project_name> <directory>        │
│           Create project in <directory> default is `.`   │
│                                                          │
│       - panther run [--reload | --help]                  │
│           Run your project with uvicorn                  │
│                                                          │
│       - panther shell [ bpython | ipython ]              │
│           Run interactive python shell                   │
│                                                          │
│       - panther monitor                                  │
│           Show the monitor :)                            │
│                                                          │
│       - panther version                                  │
│           Print the current version of Panther           │
│                                                          │
│       - panther [--help | -h ]                           │
│           Show this message and exit                     │
╰{58 * '─'}╯
"""


def cli_error(message: str | Exception) -> None:
    logger.error(message)
    logger.error('Use "panther -h" for more help')


def cli_warning(message: str | Exception, hint: str = None) -> None:
    logger.warning(message)
    if hint:
        logger.info(hint)


def cli_info(message: str) -> None:
    logger.info(message)
    logger.info('Use "panther -h" for more help\n')


def clean_args(args: list[str]) -> dict:
    """
    Input: ['--reload', '--host', '127.0.0.1', ...]
    Output: {'--reload: None, 'host': '127.0.0.1', ...}
    """
    _args = {}
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            if (i + 1) < len(args):
                _args[arg[2:]] = args[i + 1]
            else:
                _args[arg[2:]] = True
    return _args


def print_help_message():
    rprint(help_message)


def print_uvicorn_help_message():
    rprint('Run `uvicorn --help` for more help')


def print_info(config: dict):
    mo = config['monitoring']
    lq = config['log_queries']
    bt = config['background_tasks']
    ws = config['has_ws']
    bd = '{0:<39}'.format(str(config['base_dir']))
    if len(bd) > 39:
        bd = f'{bd[:36]}...'

    if config['monitoring']:
        monitor = '│ * Run "panther monitor" in another session for Monitoring│'
    else:
        monitor = f'│{58 * " "}│'

    info_message = f"""
╭{58 * '─'}╮
{logo}│{58 * ' '}│
│   Monitoring: {mo}                                  \t   │
│   Log Queries: {lq}                                 \t   │
│   Background Tasks: {bt}                            \t   │
│   Websocket: {ws}                                   \t   │
│   Base directory: {bd}│
{monitor}
╰{58 * '─'}╯
"""
    rprint(info_message)
