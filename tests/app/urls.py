from simple_apis import *

simple_api_urls = {
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

url_routing = simple_api_urls
