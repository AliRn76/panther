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
│           Create your project in current directory       │
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
│       - panther [--help | -h ]                           │
│           Show this message and exit                     │
╰{58 * '─'}╯
"""

run_help_message = """
    --host TEXT                     Bind socket to this host.  [default: 127.0.0.1]
    --port INTEGER                  Bind socket to this port.  [default: 8000]
    --uds TEXT                      Bind to a UNIX domain socket.
    --fd INTEGER                    Bind to socket from this file descriptor.
    --reload                        Enable auto-reload.
    --reload-dir PATH               Set reload directories explicitly, instead
                                    of using the current working directory.
    --reload-include TEXT           Set glob patterns to include while watching
                                    for files. Includes '*.py' by default; these
                                    defaults can be overridden with `--reload-
                                    exclude`. This option has no effect unless
                                    watchfiles is installed.
    --reload-exclude TEXT           Set glob patterns to exclude while watching
                                    for files. Includes '.*, .py[cod], .sw.*,
                                    ~*' by default; these defaults can be
                                    overridden with `--reload-include`. This
                                    option has no effect unless watchfiles is
                                    installed.
    --reload-delay FLOAT            Delay between previous and next check if
                                    application needs to be. Defaults to 0.25s.
                                    [default: 0.25]
    --workers INTEGER               Number of worker processes. Defaults to the
                                    $WEB_CONCURRENCY environment variable if
                                    available, or 1. Not valid with --reload.
    --loop [auto|asyncio|uvloop]    Event loop implementation.  [default: auto]
    --http [auto|h11|httptools]     HTTP protocol implementation.  [default: auto]
    --ws [auto|none|websockets|wsproto]
                                    WebSocket protocol implementation. [default: auto]
    --ws-max-size INTEGER           WebSocket max size message in bytes [default: 16777216]
    --ws-ping-interval FLOAT        WebSocket ping interval  [default: 20.0]
    --ws-ping-timeout FLOAT         WebSocket ping timeout  [default: 20.0]
    --ws-per-message-deflate BOOLEAN
                                    WebSocket per-message-deflate compression default: True]
    --lifespan [auto|on|off]        Lifespan implementation.  [default: auto]
    --interface [auto|asgi3|asgi2|wsgi]
                                    Select ASGI3, ASGI2, or WSGI as the
                                    application interface.  [default: auto]
    --env-file PATH                 Environment configuration file.
    --log-config PATH               Logging configuration file. Supported 
                                        formats: .ini, .json, .yaml.
    --log-level [critical|error|warning|info|debug|trace]
                                    Log level. [default: info]
    --access-log / --no-access-log  Enable/Disable access log.
    --use-colors / --no-use-colors  Enable/Disable colorized logging.
    --proxy-headers / --no-proxy-headers
                                    Enable/Disable X-Forwarded-Proto, X-Forwarded-For, 
                                    X-Forwarded-Port to populate remote address info.
    --server-header / --no-server-header
                                    Enable/Disable default Server header.
    --date-header / --no-date-header
                                    Enable/Disable default Date header.
    --forwarded-allow-ips TEXT      Comma separated list of IPs to trust with
                                    proxy headers. Defaults to the
                                    $FORWARDED_ALLOW_IPS environment variable if
                                    available, or '127.0.0.1'.
    --root-path TEXT                Set the ASGI 'root_path' for applications
                                    sub mounted below a given URL path.
    --limit-concurrency INTEGER     Maximum number of concurrent connections or
                                    tasks to allow, before issuing HTTP 503 responses.
    --backlog INTEGER               Maximum number of connections to hold in backlog
    --limit-max-requests INTEGER    Maximum number of requests to service before
                                    terminating the process.
    --timeout-keep-alive INTEGER    Close Keep-Alive connections if no new data
                                    is received within this timeout.  [default: 5]
    --ssl-keyfile TEXT              SSL key file
    --ssl-certfile TEXT             SSL certificate file
    --ssl-keyfile-password TEXT     SSL keyfile password
    --ssl-version INTEGER           SSL version to use (see stdlib ssl module's)
                                    [default: 17]
    --ssl-cert-reqs INTEGER         Whether client certificate is required 
                                    (see stdlib ssl module's)  [default: 0]
    --ssl-ca-certs TEXT             CA certificates file
    --ssl-ciphers TEXT              Ciphers to use (see stdlib ssl module's)
                                    [default: TLSv1]
    --header TEXT                   Specify custom default HTTP response headers
                                    as a Name:Value pair
    --version                       Display the uvicorn version and exit.
    --app-dir TEXT                  Look for APP in the specified directory, by
                                    adding this to the PYTHONPATH. Defaults to
                                    the current working directory.  [default: .]
    --h11-max-incomplete-event-size INTEGER
                                    For h11, the maximum number of bytes to
                                    buffer of an incomplete event.
    --factory                       Treat APP as an application factory, i.e. a
                                    () -> <ASGI app> callable.
    --help                          Show this message and exit.
    """


def cli_error(message: str | TypeError) -> None:
    logger.error(f'Error: {message}\n\nUse panther -h for more help')


def import_error_message(module_name: str) -> str:
    return f'No module named "{module_name}"\n\t    Hint: Try to install with "pip install {module_name}"'


def import_error(module_name: str) -> None:
    logger.critical(import_error_message(module_name))


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
