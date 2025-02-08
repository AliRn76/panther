from panther.middlewares import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class PublicMiddleware(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket):
        if hasattr(request, 'middlewares'):
            request.middlewares.append('Public')
        else:
            request.middlewares = ['Public']

        print(f'Hi {self.__class__.__name__}')
        return request

    async def after(self, response: Response | GenericWebsocket):
        print(f'Bye {self.__class__.__name__}')
        return response

class PrivateMiddleware(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket):
        if hasattr(request, 'middlewares'):
            request.middlewares.append('Private')
        else:
            request.middlewares = ['Private']

        print(f'Hi {self.__class__.__name__}')
        return request

    async def after(self, response: Response | GenericWebsocket):
        print(f'Bye {self.__class__.__name__}')
        return response
