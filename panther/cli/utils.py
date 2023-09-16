from panther.logger import logger

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
│       - panther shell                                    │
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

run_help_message = """Run `uvicorn --help` for more help"""


def cli_error(message: str | TypeError) -> None:
    logger.error(f'Error: {message}\n\nUse panther -h for more help')


def clean_args(args: list[str]) -> dict:
    """
    Input: ['--reload', '--host', '127.0.0.1', ...]
    Output: {'--reload: None, 'host': '127.0.0.1', ...}
    """
    _args = dict()
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            if (i + 1) < len(args):
                _args[arg[2:]] = args[i + 1]
            else:
                _args[arg[2:]] = True
    return _args
