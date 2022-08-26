from app.apis import *
from panther.app import API
from panther.response import Response


@API.get()
async def test(*args, **kwargs):
    return Response(data={'detail': 'this is for test'})

urls = {
    'none/': return_none,
    'dict/': return_dict,
    'list/': return_list,
    'tuple/': return_tuple,
    'res-dict/': return_response_dict,
    'res-none': return_response_none,
    'res-list/': return_response_list,
    'res-tuple/': return_response_tuple,
    'res-req-data/': res_request_data,
    'res-req-data-output/': res_request_data_with_output_model,
    'redis/': using_redis,
    'sql/': using_sqlalchemy,
    'test/': test,
    '': single_user,
    # 'single/': single_user,
    # 'create/': create_user,
    # 'list/': None,
    # 'delete/': ...,
}
