
async def send_404(send):
    # TODO: Work On This Func
    await send({
        'type': 'http.response.start',
        'status': 404,
        'headers': [
            [b'content-type', b'application/json'],
        ],
    })
    return await send({
        'type': 'http.response.body',
        'body': b'',
    })


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

