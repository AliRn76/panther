import importlib
import re
from traceback import TracebackException

import orjson as json

from panther import status
from panther.file_handler import File
from panther.logger import logger


async def read_body(receive, content_type) -> bytes:
    """Read and return the entire body from an incoming ASGI message."""
    body = b''
    more_body = True
    while more_body:
        message = await receive()
        # {'type': 'lifespan.startup'}
        body += message.get('body', b'')
        more_body = message.get('more_body', False)
    return body


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
    """
    ----------------------------163708487248928886496634
    Content-Disposition: form-data; name="name"

    ali
    ----------------------------163708487248928886496634
    Content-Disposition: form-data; name="image"; filename="hello.txt"
    Content-Type: text/plain

    Hello World

    ----------------------------163708487248928886496634
    Content-Disposition: form-data; name="age"

    12
    ----------------------------163708487248928886496634--
    """

    boundary = b'--' + boundary.encode()

    field_pattern = rb'(Content-Disposition: form-data; name=")(.*)("\n\n)(.*)'
    file_pattern = rb'(Content-Disposition: form-data; name=")(.*)("; filename=")(.*)("\nContent-Type: )(.*)'

    data = dict()
    for row in body.split(boundary):
        row = row.removeprefix(b'\n').removesuffix(b'\n')
        if row == b'' or row == b'--':
            continue

        if match := re.match(pattern=field_pattern, string=row):
            _, field_name, _, value = match.groups()
            data[field_name.decode('utf-8')] = value.decode('utf-8')

        else:
            file_meta_data, value = row.split(b'\n\n', 1)
            if match := re.match(pattern=file_pattern, string=file_meta_data):
                _, field_name, _, file_name, _, content_type = match.groups()
                file = File(
                    file_name=file_name.decode('utf-8'),
                    content_type=content_type.decode('utf-8'),
                    file=value,
                )
                data[field_name.decode('utf-8')] = file
                logger.warning('File support is in beta')
            else:
                logger.error('Unrecognized Pattern')

    return data


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
