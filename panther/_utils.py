import asyncio
import importlib
import logging
import re
import subprocess
import types
from collections.abc import AsyncGenerator, Callable, Generator, Iterator
from traceback import TracebackException
from typing import Any

from panther.exceptions import PantherError
from panther.file_handler import File

logger = logging.getLogger('panther')


def import_class(dotted_path: str, /) -> type[Any]:
    """
    Example:
    -------
        Input: panther.db.models.User
        Output: User (The Class)

    """
    path, name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(path)
    return getattr(module, name)


NEWLINE_CRLF = b'\r\n'  # Windows-style
NEWLINE_LF = b'\n'  # Unix/Linux-style

# Regex patterns for CRLF (Windows)
FIELD_PATTERN_CRLF = re.compile(rb'Content-Disposition: form-data; name="(.*)"\r\n\r\n(.*)', flags=re.DOTALL)
FILE_PATTERN_CRLF = re.compile(rb'Content-Disposition: form-data; name="(.*)"; filename="(.*)"\r\nContent-Type: (.*)')

# Regex patterns for LF (Linux)
FIELD_PATTERN_LF = re.compile(rb'Content-Disposition: form-data; name="(.*)"\n\n(.*)', flags=re.DOTALL)
FILE_PATTERN_LF = re.compile(rb'Content-Disposition: form-data; name="(.*)"; filename="(.*)"\nContent-Type: (.*)')


def read_multipart_form_data(boundary: str, body: bytes) -> dict:
    boundary_bytes = b'--' + boundary.encode()

    # Choose newline type and corresponding patterns
    if body.endswith(NEWLINE_CRLF):
        newline = NEWLINE_CRLF
        field_pattern = FIELD_PATTERN_CRLF
        file_pattern = FILE_PATTERN_CRLF
    else:
        newline = NEWLINE_LF
        field_pattern = FIELD_PATTERN_LF
        file_pattern = FILE_PATTERN_LF

    data = {}
    for part in body.split(boundary_bytes):
        part = part.removeprefix(newline).removesuffix(newline)

        if part in (b'', b'--'):
            continue

        if match := field_pattern.match(string=part):
            field_name, value = match.groups()
            data[field_name.decode('utf-8')] = value.decode('utf-8')
            continue

        try:
            headers, file_content = part.split(2 * newline, 1)
        except ValueError:
            logger.error('Malformed part, skipping.')
            continue

        if match := file_pattern.match(string=headers):
            field_name, file_name, content_type = match.groups()
            data[field_name.decode('utf-8')] = File(
                file_name=file_name.decode('utf-8'),
                content_type=content_type.decode('utf-8'),
                file=file_content,
            )
        else:
            logger.error('Unrecognized multipart format')

    return data


def is_function_async(func: Callable) -> bool:
    """
    Sync result is 0 --> False
    async result is 128 --> True
    """
    return bool(func.__code__.co_flags & (1 << 7))


def traceback_message(exception: Exception) -> str:
    tb = TracebackException(type(exception), exception, exception.__traceback__)
    return ''.join(tb.format(chain=False))


def reformat_code(base_dir):
    try:
        subprocess.run(['ruff', 'format', base_dir])
        subprocess.run(['ruff', 'check', '--select', 'I', '--fix', base_dir])
    except FileNotFoundError:
        raise PantherError("No module named 'ruff', Hint: `pip install ruff`")


def check_function_type_endpoint(endpoint: types.FunctionType) -> Callable:
    # Function Doesn't Have @API Decorator
    if not hasattr(endpoint, '__wrapped__'):
        raise PantherError(
            f'You may have forgotten to use `@API()` on the `{endpoint.__module__}.{endpoint.__name__}()`',
        )


def check_class_type_endpoint(endpoint: Callable) -> Callable:
    from panther.app import GenericAPI
    from panther.websocket import GenericWebsocket

    if not issubclass(endpoint, (GenericAPI, GenericWebsocket)):
        raise PantherError(
            f'You may have forgotten to inherit from `panther.app.GenericAPI` or `panther.app.GenericWebsocket` '
            f'on the `{endpoint.__module__}.{endpoint.__name__}()`',
        )


def async_next(iterator: Iterator):
    """
    The StopIteration exception is a special case in Python,
    particularly when it comes to asynchronous programming and the use of asyncio.
    This is because StopIteration is not meant to be caught in the traditional sense;
        it's used internally by Python to signal the end of an iteration.
    """
    try:
        return next(iterator)
    except StopIteration:
        raise StopAsyncIteration


async def to_async_generator(generator: Generator) -> AsyncGenerator:
    while True:
        try:
            yield await asyncio.to_thread(async_next, iter(generator))
        except StopAsyncIteration:
            break
