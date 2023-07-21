from panther import status
from panther.app import API
from panther.response import Response


@API()
async def hello_world():
    return Response(status_code=status.HTTP_200_OK)
