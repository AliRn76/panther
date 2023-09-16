import importlib
import random
import re
import string
from traceback import TracebackException
from typing import Literal

import orjson as json

from panther import status
from panther.file_handler import File
from panther.logger import logger


async def _http_response_start(send, /, headers: dict, status_code: int):
    bytes_headers = [[k.encode(), v.encode()] for k, v in (headers or {}).items()]
    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': bytes_headers,
    })


async def _http_response_body(send, /, body: any = None):
    if body is None:
        await send({'type': 'http.response.body'})
    else:
        await send({'type': 'http.response.body', 'body': body})


async def http_response(
        send,
        /,
        *,
        status_code: int,
        monitoring=None,  # type: MonitoringMiddleware | None
        headers: dict = None,
        body: bytes = None,
        exception: bool = False,
):
    if exception:
        body = json.dumps({'detail': status.status_text[status_code]})
    elif status_code == status.HTTP_204_NO_CONTENT or body == b'null':
        body = None

    if monitoring is not None:
        await monitoring.after(status_code=status_code)

    # TODO: Should we send 'access-control-allow-origin' in any case
    await _http_response_start(send, headers=headers, status_code=status_code)
    await _http_response_body(send, body=body)


def import_class(dotted_path: str, /):
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
    r"""
    ----------------------------449529189836774544725855
    \r\nContent-Disposition: form-data; name="name"\r\n\r\nali\r\n
    ----------------------------449529189836774544725855
    \r\nContent-Disposition: form-data; name="image"; filename="ali.txt"\r\nContent-Type: text/plain\r\n\r\nHello\n\r\n
    ----------------------------449529189836774544725855
    \r\nContent-Disposition: form-data; name="age"\r\n\r\n12\r\n
    ----------------------------449529189836774544725855
    --\r\n
    """

    boundary = b'--' + boundary.encode()
    new_line = b'\r\n' if body[-2:] == b'\r\n' else b'\n'

    field_pattern = rb'(Content-Disposition: form-data; name=")(.*)("' + 2 * new_line + b')(.*)'
    file_pattern = (
            rb'(Content-Disposition: form-data; name=")(.*)("; filename=")(.*)("'
            + new_line
            + b'Content-Type: )(.*)'
    )

    data = dict()
    for row in body.split(boundary):

        row = row.removeprefix(new_line).removesuffix(new_line)
        if row == b'' or row == b'--':
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


def generate_ws_connection_id() -> str:
    return ''.join(random.choices(string.ascii_letters, k=10))


def is_function_async(func) -> bool:
    """
        sync result is 0 --> False
        async result is 128 --> True
    """
    return bool(func.__code__.co_flags & (1 << 7))


def clean_traceback_message(exception) -> str:
    """
    We are ignoring packages traceback message
    """
    tb = TracebackException(type(exception), exception, exception.__traceback__)
    stack = tb.stack.copy()
    for t in stack:
        if t.filename.find('site-packages') != -1:
            tb.stack.remove(t)
    return f'{exception}\n' + ''.join(tb.format(chain=False))


def publish_to_ws_channel(connection_id: str, action: Literal['close', 'send'], data: any):
    from panther.db.connection import redis

    if redis.is_connected:
        p_data = json.dumps({'connection_id': connection_id, 'action': action, 'data': data})
        redis.publish('websocket_connections', p_data)
