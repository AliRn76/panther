import types

from panther.app import GenericAPI
from panther.configs import config
from panther.openapi.utils import ParseEndpoint
from panther.response import TemplateResponse


class OpenAPI(GenericAPI):
    @classmethod
    def get_content(cls, endpoint, method):
        parsed = ParseEndpoint(endpoint=endpoint, method=method)

        if endpoint.output_schema:
            status_code = endpoint.output_schema.status_code
            schema = endpoint.output_schema.model.schema()
        else:
            status_code = parsed.status_code
            schema = {
                'properties': {
                    k: {'default': v} for k, v in parsed.data.items()
                }
            }

        responses = {}
        if schema:
            responses = {
                'responses': {
                    status_code: {
                        'content': {
                            'application/json': {
                                'schema': schema
                            }
                        }
                    }
                }
            }
        request_body = {}
        if endpoint.input_model and method in ['post', 'put', 'patch']:
            request_body = {
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': endpoint.input_model.schema() if endpoint.input_model else {}
                        }
                    }
                }
            }

        content = {
                      'title': parsed.title,
                      'summary': endpoint.__doc__,
                      'tags': ['.'.join(endpoint.__module__.rsplit('.')[:-1]) or endpoint.__module__],
                  } | responses | request_body
        return {method: content}

    def get(self):
        paths = {}
        # TODO:
        #   Try to process the endpoint with `ast` if output_schema is None
        #   Create Component for output_schema.model and input_model
        #
        for url, endpoint in config.FLAT_URLS.items():
            if url == '':
                url = '/'
            if not url.startswith('/'):
                url = f'/{url}'
            paths[url] = {}

            if isinstance(endpoint, types.FunctionType):
                methods = endpoint.methods
                if methods is None or 'POST' in methods:
                    paths[url] |= self.get_content(endpoint, 'post')
                if methods is None or 'GET' in methods:
                    paths[url] |= self.get_content(endpoint, 'get')
                if methods is None or 'PUT' in methods:
                    paths[url] |= self.get_content(endpoint, 'put')
                if methods is None or 'PATCH' in methods:
                    paths[url] |= self.get_content(endpoint, 'patch')
                if methods is None or 'DELETE' in methods:
                    paths[url] |= self.get_content(endpoint, 'delete')
            else:
                if endpoint.post is not GenericAPI.post:
                    paths[url] |= self.get_content(endpoint, 'post')
                if endpoint.get is not GenericAPI.get:
                    paths[url] |= self.get_content(endpoint, 'get')
                if endpoint.put is not GenericAPI.put:
                    paths[url] |= self.get_content(endpoint, 'put')
                if endpoint.patch is not GenericAPI.patch:
                    paths[url] |= self.get_content(endpoint, 'patch')
                if endpoint.delete is not GenericAPI.delete:
                    paths[url] |= self.get_content(endpoint, 'delete')

        openapi_content = {
            'openapi': '3.0.0',
            'paths': paths,
            'components': {}
        }
        print(f'{openapi_content=}')
        return TemplateResponse(name='openapi.html', context={'openapi_content': openapi_content})
