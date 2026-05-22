from panther import Panther, status
from panther.app import API
from panther.response import Response


@API()
async def hello():
    return Response(
        data={'message': 'Hello from Panther'},
        status_code=status.HTTP_200_OK,
    )


url_routing = {
    '': hello,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
