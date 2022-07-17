from app.apis import single_user, create_user

from app.apis import *
from panther.app import API
from panther.response import Response


@API.get()
async def test(*args, **kwargs):
    return Response(data={'detail': 'this is for test'})

app_urls = {
    'none/': return_none,
    'dict/': return_dict,
    'list/': return_list,
    'response/': return_response_dict,
    'test/': test,
    '': single_user,
    # 'single/': single_user,
    # 'create/': create_user,
    # 'list/': None,
    # 'delete/': ...,
}
