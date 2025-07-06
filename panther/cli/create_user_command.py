import importlib.util
import os
import sys

from rich import print as rich_print
from rich.console import Console
from rich.prompt import Prompt

from panther.cli.utils import cli_error
from panther.configs import config
from panther.db.models import BaseUser
from panther.utils import run_coroutine


def get_password(prompt: str) -> str:
    rich_print(f'[b]{prompt}: [/b]', end='', flush=True)
    password = ''

    if sys.platform == 'win32':
        import msvcrt

        while True:
            ch = msvcrt.getch()
            if ch in (b'\r', b'\n'):
                print()
                break
            elif ch == b'\x08':  # Backspace
                if password:
                    password = password[:-1]
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == b'\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                try:
                    char = ch.decode()
                    password += char
                    sys.stdout.write('*')
                    sys.stdout.flush()
                except UnicodeDecodeError:
                    continue
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    print()
                    break
                elif ch == '\x7f':  # Backspace
                    if password:
                        password = password[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    password += ch
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return password


def get_username(prompt: str, user_model: BaseUser, username_field: str):
    console = Console(style='bold')
    username = Prompt.ask(prompt=prompt, console=console)
    while run_coroutine(user_model.exists({username_field: username})):
        console.print(f'{user_model.__name__} with this {username_field} already exists.', style='bold red')
        username = Prompt.ask(prompt=prompt, console=console)
    return username


def load_application_file(file_location: str):
    file_name = file_location.removesuffix('.py')
    script_path = os.path.abspath(path=file_location)
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(name=file_name, location=file_location)
    mod = importlib.util.module_from_spec(spec=spec)
    spec.loader.exec_module(module=mod)


def create_user(args) -> None:
    if len(args) == 0:
        return cli_error(
            'Not Enough Arguments, Give me a file path that contains `Panther()` app.\n'
            '       * Make sure to run `panther createuser` in the same directory as that file!\n'
            '       * Example: `panther createuser main.py`',
        )
    elif len(args) != 1:
        return cli_error('Too Many Arguments.')
    load_application_file(file_location=args[0])
    # Initialization
    User: BaseUser = config.USER_MODEL
    user_model_name = User.__name__
    username_field = User.USERNAME_FIELD
    console = Console()
    try:
        username = get_username(f'Enter your `{username_field}`', user_model=User, username_field=username_field)
        password = get_password('Enter your `password`')
    except KeyboardInterrupt:
        console.print('\nKeyboard Interrupt', style='bold red')
        return

    # Creating User
    user = run_coroutine(User.insert_one({username_field: username}))
    run_coroutine(user.set_password(password=password))
    console.print(f'\n{user_model_name}({username_field}={username}) Created Successfully.', style='bold green')
