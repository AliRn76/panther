import importlib
import re
from traceback import TracebackException

import orjson as json

from panther import status
from panther.file_handler import File
from panther.logger import logger


async def read_body(receive) -> bytes:
    """Read and return the entire body from an incoming ASGI message."""
    body = b''
    more_body = True
    while more_body:
        message = await receive()
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
        monitoring,  # type: MonitoringMiddleware | None
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


def read_multipart_form_data(content_type: str, body: str) -> dict:
    """
    content_type = 'multipart/form-data; boundary=--------------------------984465134948354357674418'
    """
    boundary = content_type[30:]

    pre_pattern = r'(.*\r\nContent-Disposition: form-data; name=")(.*)'  # (Junk)(FieldName)
    field_value_pattern = r'"(\r\n\r\n)(.*)'  # (Junk)(Value)
    file_value_pattern = r'(\r\n\r\n)(.*)(\n\r\n--)'  # (Junk)(Value)(Junk)

    # (Junk)(FieldName) + (Junk)(Value)(Junk) + (Junk)
    field_pattern = pre_pattern + field_value_pattern + r'(\r\n.*)'

    # (Junk)(FieldName) + (Junk)(FileName)(Junk)(ContentType) + (Junk)(Value)
    file_pattern = pre_pattern + r'("; filename=")(.*)("\r\nContent-Type: )(.*)' + file_value_pattern

    fields = dict()
    for field in body.split(boundary):
        if match := re.match(pattern=field_pattern, string=field):
            _, field_name, _, value, _ = match.groups()
            fields[field_name] = value

        if match := re.match(pattern=file_pattern, string=field, flags=re.DOTALL):
            _, field_name, _, file_name, _, content_type, _, value, _ = match.groups()
            file = File(
                file_name=file_name,
                content_type=content_type,
                file=value,
            )
            fields[field_name] = file
            logger.error('File support is in beta')
    return fields


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
