import logging
import platform

from rich import print as rprint

from panther.configs import Config
from panther.exceptions import PantherError

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

top = f'{tl}{60 * v}{tr}'
bottom = f'{bl}{60 * v}{br}'

logo = rf"""{top}
{h}     ____                 __    __                          {h}
{h}    /\  _`\              /\ \__/\ \                         {h}
{h}    \ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __      {h}
{h}     \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\    {h}
{h}      \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/     {h}
{h}       \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\     {h}
{h}        \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/     {h}
{h}                                                            {h}"""

help_message = rf"""{logo}
{h}   Usage: panther <command> \[options]                       {h}
{h}                                                            {h}
{h}   Commands:                                                {h}
{h}       - create \[project_name] \[directory]                  {h}
{h}           Create a new Panther project.                    {h}
{h}           * Interactive mode if no arguments provided.     {h}
{h}           * Non-interactive if project_name and directory  {h}
{h}             are specified (default directory: .).          {h}
{h}           Example:                                         {h}
{h}               - `panther create`                           {h}
{h}               - `panther create myapp myapp`               {h}
{h}                                                            {h}
{h}       - run <app> \[options]                                {h}
{h}           Run your Panther project using Uvicorn.          {h}
{h}           * app: address of your application.              {h}
{h}           * options: Check `uvicorn --help` for options.   {h}
{h}           * `panther run` is alias of `uvicorn`.           {h}
{h}           Example: `panther run main:app --reload`         {h}
{h}                                                            {h}
{h}       - shell <application_file>                           {h}       
{h}           Start an interactive Python shell with your app. {h}
{h}           * application_file: path to your main app file.  {h}           
{h}           Example: `panther shell main.py`                 {h}
{h}                                                            {h}
{h}       - createuser <application_file>                      {h}       
{h}           Create a new user based on USER_MODEl from your, {h}
{h}           configs. (default is panther.db.models.BaseUser) {h}
{h}           * application_file: path to your main app file.  {h}           
{h}           Example: `panther createuser main.py`            {h}
{h}                                                            {h}
{h}       - monitor                                            {h}
{h}           Display real-time request monitoring.            {h}
{h}                                                            {h}
{h}       - version | --version                                {h}
{h}           Display the current version of Panther.          {h}
{h}                                                            {h}
{h}       - help | h | --help | -h                             {h}
{h}           Show this help message and exit.                 {h}
{bottom}
"""


def import_error(message: str | Exception, package: str | None = None) -> PantherError:
    msg = str(message)
    if package:
        msg += f' -> Hint: `pip install {package}`'
    return PantherError(msg)


def cli_error(message: str | Exception) -> None:
    logger.error(message)
    logger.info('Use "panther -h" for more help')


def cli_warning(message: str | Exception, hint: str = None) -> None:
    logger.warning(message)
    if hint:
        logger.info(hint)


def cli_info(message: str) -> None:
    logger.info(message)
    logger.info('Use "panther -h" for more help\n')


def print_help_message():
    rprint(help_message)


def print_info(config: Config):
    from panther.db.connections import redis

    mo = config.MONITORING
    lq = config.LOG_QUERIES
    bt = config.BACKGROUND_TASKS
    ws = config.HAS_WS
    rd = redis.is_connected
    bd = f'{config.BASE_DIR!s:<41}'
    if len(bd) > 41:
        bd = f'{bd[:38]}...'

    # Monitoring
    monitor = f'{h} * Run "panther monitor" in another session for Monitoring  {h}\n' if config.MONITORING else None

    # Uvloop
    uvloop_msg = None
    if platform.system() != 'Windows':
        try:
            import uvloop
        except ImportError:
            uvloop_msg = (
                f'{h} * You may want to install `uvloop` for better performance  {h}\n'
                f'{h}   `pip install uvloop`                                     {h}\n'
            )

    # Gunicorn if Websocket
    gunicorn_msg = None
    if config.HAS_WS:
        try:
            import gunicorn

            gunicorn_msg = f'{h} * You have WS, so make sure to run gunicorn with --preload  {h}\n'
        except ImportError:
            pass

    # Message
    info_message = f"""{logo}
{h}   Redis: {rd}                                       \t     {h}
{h}   Websocket: {ws}                                   \t     {h}
{h}   Monitoring: {mo}                                  \t     {h}
{h}   Log Queries: {lq}                                 \t     {h}
{h}   Background Tasks: {bt}                            \t     {h}
{h}   Base directory: {bd}{h}
"""
    if monitor:
        info_message += monitor
    if uvloop_msg:
        info_message += uvloop_msg
    if gunicorn_msg:
        info_message += gunicorn_msg

    info_message += bottom
    rprint(info_message)
