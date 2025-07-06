import importlib.util
import os
import sys
import termios
import tty

from rich import print as rich_print
from rich.console import Console
from rich.prompt import Prompt

from panther.cli.utils import cli_error
from panther.configs import config
from panther.db.models import BaseUser
from panther.utils import run_coroutine


def get_password(prompt: str):
    rich_print(f'[b]{prompt}: [/b]', end='')
    password = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\n" or ch == "\r":
                print()  # Newline after Enter
                break
            elif ch == "\x7f":  # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            else:
                password += ch
                sys.stdout.write("*")
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return password


def load_file(file_location: str):
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

    load_file(file_location=args[0])

    # Initialization
    User: BaseUser = config.USER_MODEL
    user_model_name = User.__name__
    username_field = User.USERNAME_FIELD
    console = Console()
    input_console = Console(style='bold')

    try:
        # Get Username
        username = Prompt.ask(f'Enter your `{username_field}`', console=input_console)
        while run_coroutine(User.exists({username_field: username})):
            console.print(f'{user_model_name} with this {username_field} already exists.', style='bold red')
            username = Prompt.ask(f'Enter your `{username_field}`', console=input_console)

        # Get Password
        password = get_password('Enter your `password`')
    except KeyboardInterrupt:
        console.print('\nKeyboard Interrupt', style='bold red')
        return

    # Creating User
    user = run_coroutine(User.insert_one({username_field: username}))
    run_coroutine(user.set_password(password=password))
    console.print(f'\n{user_model_name}({username_field}={username}) Created Successfully.', style='bold green')
