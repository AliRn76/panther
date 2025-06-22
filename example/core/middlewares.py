from panther.middlewares import HTTPMiddleware
from panther.request import Request


class PublicMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request):
        if hasattr(request, 'middlewares'):
            request.middlewares.append('Public')
        else:
            request.middlewares = ['Public']
        print(f'Hi {self.__class__.__name__}')
        response = await self.dispatch(request=request)
        print(f'Bye {self.__class__.__name__}')
        return response


class PrivateMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request):
        if hasattr(request, 'middlewares'):
            request.middlewares.append('Private')
        else:
            request.middlewares = ['Private']
        print(f'Hi {self.__class__.__name__}')
        response = await self.dispatch(request=request)
        print(f'Bye {self.__class__.__name__}')
        return response
