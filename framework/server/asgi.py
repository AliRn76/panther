from contextlib


class Asgi:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        assert scope['type'] == 'http'
        ...
