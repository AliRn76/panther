import asyncio
import importlib
import inspect
import logging
import mimetypes
import re
import subprocess
import traceback
import types
from collections.abc import AsyncGenerator, Callable, Generator, Iterator
from datetime import timedelta
from traceback import TracebackException
from typing import Any

from panther.exceptions import PantherError
from panther.file_handler import File

logger = logging.getLogger('panther')

ENDPOINT_FUNCTION_BASED_API = 0
ENDPOINT_CLASS_BASED_API = 1
ENDPOINT_WEBSOCKET = 2


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


def check_function_type_endpoint(endpoint: types.FunctionType):
    # Function Doesn't Have @API Decorator
    if not hasattr(endpoint, '__wrapped__'):
        raise PantherError(
            f'You may have forgotten to use `@API()` on the `{endpoint.__module__}.{endpoint.__name__}()`',
        )


def check_class_type_endpoint(endpoint: Callable):
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


def validate_api_auth(auth):
    """Validate the auth callable or class for correct async signature and argument count."""
    if auth is None:
        return None

    if not callable(auth):
        msg = (
            f'`{type(auth).__name__}` is not valid for authentication, it should be a callable, a Class with __call__ '
            f'method or a single function.'
        )
        logger.error(msg)
        raise PantherError(msg)

    # If it's a class, validate its __call__
    if inspect.isclass(auth):
        call_method = getattr(auth, '__call__', None)
        if not inspect.isfunction(call_method):
            msg = f'{auth.__name__} must implement __call__() method.'
            logger.error(msg)
            raise PantherError(msg)
        func = call_method
        expected_args = 2  # self, request
        func_name = f'{auth.__name__}.__call__()'
    else:
        func = auth
        expected_args = 1  # request
        func_name = f'{auth.__name__}()'

    sig = inspect.signature(func)
    if len(sig.parameters) != expected_args:
        msg = f'{func_name} requires {expected_args} positional argument(s) ({"self, " if expected_args == 2 else ""}request).'
        logger.error(msg)
        raise PantherError(msg)

    # Check if async
    if not is_function_async(func):
        msg = f'{func_name} should be `async`'
        logger.error(msg)
        raise PantherError(msg)


def validate_api_permissions(permissions):
    if permissions is None:
        return permissions

    for perm in permissions:
        if not callable(perm):
            msg = (
                f'`{type(perm).__name__}` is not valid for permission, it should be a callable, a Class with __call__ '
                f'method or a single function.'
            )
            logger.error(msg)
            raise PantherError(msg)

        # If it's a class, validate its __call__
        if inspect.isclass(perm):
            call_method = getattr(perm, '__call__', None)
            if not inspect.isfunction(call_method):
                msg = f'{perm.__name__} must implement __call__() method.'
                logger.error(msg)
                raise PantherError(msg)
            func = call_method
            expected_args = 2  # self, request
            func_name = f'{perm.__name__}.__call__()'
        else:
            func = perm
            expected_args = 1  # request
            func_name = f'{perm.__name__}()'

        sig = inspect.signature(func)
        if len(sig.parameters) != expected_args:
            msg = f'{func_name} requires {expected_args} positional argument(s) ({"self, " if expected_args == 2 else ""}request).'
            logger.error(msg)
            raise PantherError(msg)

        # Check if async
        if not is_function_async(func):
            msg = f'{func_name} should be `async`'
            logger.error(msg)
            raise PantherError(msg)


def check_api_deprecations(cache, **kwargs):
    # Check Cache Usage
    if kwargs.pop('cache_exp_time', None):
        deprecation_message = (
            traceback.format_stack(limit=2)[0]
            + '\nThe `cache_exp_time` argument has been removed in Panther v5 and is no longer available.'
            '\nYou may want to use `cache` instead.'
        )
        raise PantherError(deprecation_message)
    if cache and not isinstance(cache, timedelta):
        deprecation_message = (
            traceback.format_stack(limit=2)[0] + '\nThe `cache` argument has been changed in Panther v5, '
            'it should be an instance of `datetime.timedelta()`.'
        )
        raise PantherError(deprecation_message)
    # Check Others
    if kwargs:
        msg = f'Unknown kwargs: {kwargs.keys()}'
        logger.error(msg)
        raise PantherError(msg)


def detect_mime_type(file_path: str) -> str:
    # Try extension-based detection
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    # Try content-based detection (magic numbers)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            if header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif header.startswith(b'%PDF'):
                return 'application/pdf'
            elif header.startswith(b'PK\x03\x04'):
                return 'application/zip'
            elif header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return 'image/gif'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            elif header.startswith(b'\x00\x00\x01\x00'):
                return 'image/x-icon'  # ICO file
            elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
                return 'image/tiff'
            elif header[:4] == b'\x00\x00\x00\x18' and b'ftyp' in header:
                return 'video/mp4'
    except Exception:
        pass

    # Fallback if no match
    return 'application/octet-stream'
