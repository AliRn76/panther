from panther import version, status
from panther.app import API
from panther.configs import config
from panther.request import Request
from panther.response import Response


@API()
async def hello_world():
    return Response(status_code=200)
