import contextlib
import sys

import uvicorn

from panther.cli.utils import cli_error


def run(args: list[str]) -> None:
    try:
        with contextlib.suppress(KeyboardInterrupt):
            # First arg will be ignored by @Click, so ...
            sys.argv = ['main'] + args
            uvicorn.main()
    except TypeError as e:
        cli_error(e)
