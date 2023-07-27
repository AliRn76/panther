import re
import importlib

import orjson as json

from panther.logger import logger
from panther.status import status_text


async def read_body(receive) -> bytes:
    """Read and return the entire body from an incoming ASGI message."""
    body = b''
    more_body = True
    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)
    return body


async def _http_response_start(send, /, status_code: int):
    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': [
            [b'content-type', b'application/json'],
        ],
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
        body: bytes = None,
        exception: bool = False
):
    if exception:
        body = json.dumps({'detail': status_text[status_code]})
    elif status_code == 204 or body == b'null':
        body = None

    if monitoring is not None:
        await monitoring.after(status_code=status_code)

    await _http_response_start(send, status_code=status_code)
    await _http_response_body(send, body=body)


def import_class(dotted_path: str, /):
    """
    Example:
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

    pre_pattern = r'(.*\r\nContent-Disposition: form-data; name=")(.*)"'  # (Junk)(FieldName)"
    value_pattern = r'(\r\n\r\n)(.*)'  # (Junk)(Value)

    # (Junk)(FieldName) (Junk)(Value)(Junk)
    field_pattern = pre_pattern + value_pattern + r'(\r\n.*)'

    # (Junk)(FieldName) (Junk)(FileName)(Junk)(ContentType) (Junk)(Value)
    file_pattern = pre_pattern + r'("; filename=")(.*)("\r\nContent-Type: )(.*)' + value_pattern

    fields = dict()
    for field in body.split(boundary):
        if match := re.match(pattern=field_pattern, string=field):
            _, field_name, _, value, _ = match.groups()
            fields[field_name] = value

        if match := re.match(pattern=file_pattern, string=field):
            # TODO: It works but it is not profitable, So comment it for later
            #   We should handle it while we are reading the body in _utils.read_body()

            # _, field_name, _, file_name, _, content_type, _, value = match.groups()
            # data = {
            #     'filename': file_name,
            #     'Content-Type': content_type,
            #     'value': value
            # }
            # fields[field_name] = data
            logger.error("We Don't Handle Files In Multipart Request Yet.")
    return fields
