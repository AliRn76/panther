from simple_response_apis import *
from simple_request_apis import *
from method_apis import *


simple_responses_urls = {
    'nothing': return_nothing,
    'none': return_none,
    'dict': return_dict,
    'list': return_list,
    'tuple': return_tuple,
    'response-none': return_response_none,
    'response-dict': return_response_dict,
    'response-list': return_response_list,
    'response-tuple': return_response_tuple,
}

simple_requests_urls = {
    'request-header': request_header,
    'request-path': request_path,
    'request-client': request_client,
    'request-query_params': request_query_params,
    'request-data': request_data,
}

method_urls = {
    'all': request_all,
    'get': request_get,
    'post': request_post,
    'put': request_put,
    'patch': request_patch,
    'delete': request_delete,
    'get-post-patch': request_get_post_patch,
}

url_routing = simple_responses_urls | simple_requests_urls | method_urls
