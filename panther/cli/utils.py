import logging
import platform

from rich import print as rprint


logger = logging.getLogger('panther')


if platform.system() == 'Windows':
    h = '|'
    v = '_'
    tr = ' '
    tl = ' '
    br = ' '
    bl = ' '
else:
    h = '│'
    v = '─'
    tr = '╮'
    tl = '╭'
    br = '╯'
    bl = '╰'

top = f'{tl}{58 * v}{tr}'
bottom = f'{bl}{58 * v}{br}'

logo = rf"""{top}
{h}    ____                 __    __                         {h}
{h}   /\  _`\              /\ \__/\ \                        {h}
{h}   \ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __     {h}
{h}    \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\   {h}
{h}     \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/    {h}
{h}      \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\    {h}
{h}       \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/    {h}
{h}                                                          {h}"""

help_message = f"""{logo}
{h}   usage:                                                 {h}
{h}       - panther create <project_name> <directory>        {h}
{h}           Create project in <directory> default is `.`   {h}
{h}                                                          {h}
{h}       - panther run [--reload | --help]                  {h}
{h}           Run your project with uvicorn                  {h}
{h}                                                          {h}
{h}       - panther shell [ bpython | ipython ]              {h}
{h}           Run interactive python shell                   {h}
{h}                                                          {h}
{h}       - panther monitor                                  {h}
{h}           Show the monitor :)                            {h}
{h}                                                          {h}
{h}       - panther version                                  {h}
{h}           Print the current version of Panther           {h}
{h}                                                          {h}
{h}       - panther h | help | --help | -h                   {h}
{h}           Show this message and exit                     {h}
{bottom}
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

    # Monitoring
    if config['monitoring']:
        monitor = f'{h} * Run "panther monitor" in another session for Monitoring{h}\n'
    else:
        monitor = None

    # Uvloop
    if platform.system() != 'Windows':
        try:
            import uvloop
            uvloop = None
        except ImportError:
            uvloop = (
                f'{h} * You may want to install `uvloop` for better performance{h}\n'
                f'{h}   `pip install uvloop`                                   {h}\n')
    else:
        uvloop = None

    # Message
    info_message = f"""{logo}
{h}   Monitoring: {mo}                                  \t   {h}
{h}   Log Queries: {lq}                                 \t   {h}
{h}   Background Tasks: {bt}                            \t   {h}
{h}   Websocket: {ws}                                   \t   {h}
{h}   Base directory: {bd}{h}
"""
    if monitor:
        info_message += monitor
    if uvloop:
        info_message += uvloop
    info_message += bottom
    rprint(info_message)
