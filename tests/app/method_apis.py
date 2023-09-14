from panther.app import API
from panther.response import Response


@API()
async def request_all():
    return Response()


@API(methods=['GET'])
async def request_get():
    return Response()


@API(methods=['POST'])
async def request_post():
    return Response()


@API(methods=['PUT'])
async def request_put():
    return Response()


@API(methods=['PATCH'])
async def request_patch():
    return Response()


@API(methods=['DELETE'])
async def request_delete():
    return Response()


@API(methods=['GET', 'POST', 'PATCH'])
async def request_get_post_patch():
    return Response()
