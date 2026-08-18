import contextlib
import importlib
import os
import sys

from panther.cli.utils import cli_error

UVICORN_SERVER = 'uvicorn'
RUST_SERVER = 'rust'
SERVERS = (UVICORN_SERVER, RUST_SERVER)


def split_server_option(args: list[str]) -> tuple[str, list[str]]:
    """Pull `--server <name>` (or `--server=<name>`) out of `args`.

    Everything else is passed through untouched so the default uvicorn path
    keeps accepting the full uvicorn option set.
    """
    server = UVICORN_SERVER
    remaining = []
    index = 0

    while index < len(args):
        argument = args[index]
        if argument == '--server':
            if index + 1 >= len(args):
                raise ValueError(f'`--server` requires a value, one of: {", ".join(SERVERS)}')
            server = args[index + 1]
            index += 2
            continue
        if argument.startswith('--server='):
            server = argument.split('=', maxsplit=1)[1]
            index += 1
            continue
        remaining.append(argument)
        index += 1

    if server not in SERVERS:
        raise ValueError(f'Unknown server {server!r}, expected one of: {", ".join(SERVERS)}')

    return server, remaining


def parse_rust_options(args: list[str]) -> tuple[str, dict]:
    """Parse the option subset the Rust server understands.

    Returns the application address (e.g. `main:app`) and the keyword arguments
    for `panther.server.run()`.
    """
    address = None
    options = {
        'host': '127.0.0.1',
        'port': 8000,
        'root_path': '',
        'workers': None,
        'lifespan': True,
    }
    integer_options = {'--port': 'port', '--workers': 'workers'}
    string_options = {'--host': 'host', '--root-path': 'root_path'}

    index = 0
    while index < len(args):
        argument = args[index]

        if argument.startswith('--') and '=' in argument:
            argument, value = argument.split('=', maxsplit=1)
            args = [*args[:index], argument, value, *args[index + 1 :]]

        if argument == '--no-lifespan':
            options['lifespan'] = False
            index += 1
            continue

        if argument in integer_options or argument in string_options:
            if index + 1 >= len(args):
                raise ValueError(f'`{argument}` requires a value')
            value = args[index + 1]
            if argument in integer_options:
                if not value.lstrip('-').isdigit():
                    raise ValueError(f'`{argument}` expects an integer, got {value!r}')
                options[integer_options[argument]] = int(value)
            else:
                options[string_options[argument]] = value
            index += 2
            continue

        if argument.startswith('-'):
            raise ValueError(f'`{argument}` is not supported by the Rust server (yet)')

        if address is not None:
            raise ValueError(f'Too many application addresses: {address!r} and {argument!r}')
        address = argument
        index += 1

    if address is None:
        raise ValueError(
            'Give me the address of your application.\n       * Example: `panther run --server rust main:app`',
        )

    return address, options


def load_app(address: str):
    """Resolve `module:attribute` the same way uvicorn does."""
    if ':' not in address:
        raise ValueError(f'Invalid application address {address!r}, expected `module:attribute`')

    module_name, _, attribute_path = address.partition(':')
    module_name = module_name.removesuffix('.py').replace('/', '.')

    if (cwd := os.getcwd()) not in sys.path:
        sys.path.insert(0, cwd)

    try:
        application = importlib.import_module(module_name)
    except ImportError as exception:
        raise ValueError(f'Cannot import {module_name!r}: {exception}') from exception

    for attribute in attribute_path.split('.'):
        try:
            application = getattr(application, attribute)
        except AttributeError as exception:
            raise ValueError(f'{module_name!r} has no attribute {attribute_path!r}') from exception

    return application


def run(args: list[str]) -> None:
    try:
        server, args = split_server_option(args)
    except ValueError as exception:
        return cli_error(exception)

    if server == RUST_SERVER:
        return run_with_rust(args)

    return run_with_uvicorn(args)


def run_with_uvicorn(args: list[str]) -> None:
    import uvicorn

    try:
        with contextlib.suppress(KeyboardInterrupt):
            # First arg will be ignored by @Click, so ...
            sys.argv = ['main'] + args
            uvicorn.main()
    except TypeError as e:
        cli_error(e)


def run_with_rust(args: list[str]) -> None:
    from panther.exceptions import PantherError
    from panther.server import run as rust_run

    try:
        address, options = parse_rust_options(args)
        application = load_app(address)
    except ValueError as exception:
        return cli_error(exception)

    try:
        rust_run(application, **options)
    except PantherError as exception:
        return cli_error(exception.args[0] if exception.args else exception)
