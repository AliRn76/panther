from panther.app import API
from panther.response import Response


@API()
async def return_nothing():
    pass


@API()
async def return_none():
    return None


@API()
async def return_dict():
    return {'detail': 'ok'}


@API()
async def return_list():
    return [1, 2, 3]


@API()
async def return_tuple():
    return 1, 2, 3, 4


@API()
async def return_response_none():
    return Response()


@API()
async def return_response_dict():
    return Response(data={'detail': 'ok'})


@API()
async def return_response_list():
    return Response(data=['car', 'home', 'phone'])


@API()
async def return_response_tuple():
    return Response(data=('car', 'home', 'phone', 'book'))
