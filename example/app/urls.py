from app.apis import *
from app.websockets import UserWebsocket

from panther.app import API
from panther.response import Response


@API()
async def test(*args, **kwargs):
    return Response(data={'detail': 'this is for test'})


urls = {
    'none-class/': ReturnNone,
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
    'login/': login,
    'auth/': auth_true,
    'perm/': check_permission,
    'rate-limit/': rate_limit,
    'test/': test,
    'patch-user/': patch_user,
    'patch-user-class/': PatchUser,
    'file-class/': FileAPI,
    'html-response/': HTMLAPI,
    'template-response/': TemplateAPI,
    '': single_user,
    'ws/<user_id>/': UserWebsocket,
    'send/<connection_id>/': send_message_to_websocket_api,
    'bg-tasks/': run_background_tasks_api,
    'custom-response/': custom_response_class_api,
    'image/': ImageAPI,
    'logout/': logout_api,
    'stream/': stream_api,
    'pagination/': PaginationAPI,
    'middleware': detect_middlewares,
}
