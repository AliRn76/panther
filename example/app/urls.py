from app.apis import *  # NOQA: F403

from panther.app import API
from panther.response import Response


@API()
async def test(*args, **kwargs):
    return Response(data={'detail': 'this is for test'})

urls = {
    'none-class/': ReturnNone,  # NOQA: F405
    'none/': return_none,  # NOQA: F405
    'dict/': return_dict,  # NOQA: F405
    'list/': return_list,  # NOQA: F405
    'tuple/': return_tuple,  # NOQA: F405
    'res-dict/': return_response_dict,  # NOQA: F405
    'res-none': return_response_none,  # NOQA: F405
    'res-list/': return_response_list,  # NOQA: F405
    'res-tuple/': return_response_tuple,  # NOQA: F405
    'res-req-data/': res_request_data,  # NOQA: F405
    'res-req-data-output/': res_request_data_with_output_model,  # NOQA: F405
    'redis/': using_redis,  # NOQA: F405
    'login/': login,  # NOQA: F405
    'auth/': auth_true,  # NOQA: F405
    'perm/': check_permission,  # NOQA: F405
    'rate-limit/': rate_limit,  # NOQA: F405
    'test/': test,  # NOQA: F405
    'patch-user/': patch_user,  # NOQA: F405
    'patch-user-class/': PatchUser,  # NOQA: F405
    '': single_user,  # NOQA: F405
}
