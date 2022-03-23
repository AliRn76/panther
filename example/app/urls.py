from app.apis import single_user, create_user

from panther.app import API
from panther.response import Response


@API.get()
async def test(*args, **kwargs):
    return Response(data={'detail': 'this is for test'})

app_urls = {
    '': test,
    # 'single/': single_user,
    # 'create/': create_user,
    # 'list/': None,
    # 'delete/': ...,
}
