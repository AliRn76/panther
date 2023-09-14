from panther.app import API
from panther.request import Request


@API()
async def request_header(request: Request):
    return request.headers.__dict__


@API()
async def request_path(request: Request):
    return request.path


@API()
async def request_client(request: Request):
    return request.client


@API()
async def request_query_params(request: Request):
    return request.query_params


@API()
async def request_data(request: Request):
    return request.data
