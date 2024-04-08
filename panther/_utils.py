import asyncio
import importlib
import logging
import re
import subprocess
import types
from typing import Any, Generator, Iterator, AsyncGenerator
from collections.abc import Callable
from traceback import TracebackException

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


def read_multipart_form_data(boundary: str, body: bytes) -> dict:
    boundary = b'--' + boundary.encode()
    new_line = b'\r\n' if body[-2:] == b'\r\n' else b'\n'

    field_pattern = (
            rb'(Content-Disposition: form-data; name=")(.*)("'
            + 2 * new_line
            + b')(.*)'
    )
    file_pattern = (
            rb'(Content-Disposition: form-data; name=")(.*)("; filename=")(.*)("'
            + new_line
            + b'Content-Type: )(.*)'
    )

    data = {}
    for _row in body.split(boundary):
        row = _row.removeprefix(new_line).removesuffix(new_line)

        if row in (b'', b'--'):
            continue

        if match := re.match(pattern=field_pattern, string=row):
            _, field_name, _, value = match.groups()
            data[field_name.decode('utf-8')] = value.decode('utf-8')

        else:
            file_meta_data, value = row.split(2 * new_line, 1)

            if match := re.match(pattern=file_pattern, string=file_meta_data):
                _, field_name, _, file_name, _, content_type = match.groups()
                file = File(
                    file_name=file_name.decode('utf-8'),
                    content_type=content_type.decode('utf-8'),
                    file=value,
                )
                data[field_name.decode('utf-8')] = file
            else:
                logger.error('Unrecognized Pattern')

    return data


def is_function_async(func: Callable) -> bool:
    """
    Sync result is 0 --> False
    async result is 128 --> True
    """
    return bool(func.__code__.co_flags & (1 << 7))


def clean_traceback_message(exception: Exception) -> str:
    """We are ignoring packages traceback message"""
    tb = TracebackException(type(exception), exception, exception.__traceback__)
    stack = tb.stack.copy()
    for t in stack:
        if t.filename.find('site-packages/panther') != -1 or t.filename.find('site-packages\\panther') != -1:
            tb.stack.remove(t)
    _traceback = list(tb.format(chain=False))
    return exception if len(_traceback) == 1 else f'{exception}\n' + ''.join(_traceback)


def reformat_code(base_dir):
    try:
        subprocess.run(['ruff', 'format', base_dir])
        subprocess.run(['ruff', 'check', '--select', 'I', '--fix', base_dir])
    except FileNotFoundError:
        raise PantherError("No module named 'ruff', Hint: `pip install ruff`")


def check_function_type_endpoint(endpoint: types.FunctionType) -> Callable:
    # Function Doesn't Have @API Decorator
    if not hasattr(endpoint, '__wrapped__'):
        logger.critical(f'You may have forgotten to use @API() on the {endpoint.__name__}()')
        raise TypeError
    return endpoint


def check_class_type_endpoint(endpoint: Callable) -> Callable:
    from panther.app import GenericAPI

    if not issubclass(endpoint, GenericAPI):
        logger.critical(f'You may have forgotten to inherit from GenericAPI on the {endpoint.__name__}()')
        raise TypeError

    return endpoint().call_method


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
