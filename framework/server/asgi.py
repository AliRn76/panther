from contextlib import AsyncExitStack


class Asgi:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        self.app(scope)
