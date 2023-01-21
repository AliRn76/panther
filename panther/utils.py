import importlib
import orjson as json
from panther.status import status_text


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


async def http_response(send, /, *, status_code: int, monitoring: any, body: bytes = None, exception: bool = False):
    # TODO: Handle MonitoringMiddleware type (we should move it not fix :) Think about it later)
    if exception:
        body = json.dumps({'detail': status_text[status_code]})
    elif status_code == 204 or body == b'null':
        body = None
    await monitoring.after(status_code=status_code)
    await _http_response_start(send, status_code=status_code)
    await _http_response_body(send, body=body)


async def read_body(receive) -> bytes:
    """
    Read and return the entire body from an incoming ASGI message.
    """
    body = b''
    more_body = True
    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)
    return body


def import_class(_klass: str, /):
    """
    Example:
        Input: panther.db.models.User
        Output: User (The Class)
    """
    seperator = _klass.rfind('.')
    module = importlib.import_module(_klass[:seperator])
    return getattr(module, _klass[seperator + 1:])
