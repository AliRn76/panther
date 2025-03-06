import types

from panther.app import GenericAPI
from panther.configs import config
from panther.response import TemplateResponse


class OpenAPI(GenericAPI):
    @classmethod
    def get_content(cls, endpoint):
        return {
            'summary': endpoint.__doc__,
            'tags': [endpoint.__module__],
            'responses': {
                endpoint.output_schema.status_code: {
                    'content': {
                        'application/json': {
                            'schema': endpoint.output_schema.model.schema() if endpoint.output_schema.model else {}
                        }
                    }
                }
            } if endpoint.output_schema else {},
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': endpoint.input_model.schema()
                    }
                }
            } if endpoint.input_model else {}
        }

    def get(self):
        paths = {}
        # TODO:
        #   Try to process the endpoint with `ast` if output_schema is None
        #   Create Component for output_schema.model and input_model
        #
        for url, endpoint in config.FLAT_URLS.items():
            if endpoint is OpenAPI:
                continue
            if url == '':
                url = '/'
            if not url.startswith('/'):
                url = f'/{url}'
            paths[url] = {}

            if isinstance(endpoint, types.FunctionType):
                methods = endpoint.methods
                if methods is None or 'POST' in methods:
                    paths[url]['post'] = self.get_content(endpoint)
                if methods is None or 'GET' in methods:
                    paths[url]['get'] = self.get_content(endpoint)
                if methods is None or 'PUT' in methods:
                    paths[url]['put'] = self.get_content(endpoint)
                if methods is None or 'patch' in methods:
                    paths[url]['patch'] = self.get_content(endpoint)
                if methods is None or 'delete' in methods:
                    paths[url]['delete'] = self.get_content(endpoint)
            else:
                if endpoint.post is not GenericAPI.post:
                    paths[url]['post'] = self.get_content(endpoint)
                elif endpoint.get is not GenericAPI.get:
                    paths[url]['get'] = self.get_content(endpoint)
                elif endpoint.put is not GenericAPI.put:
                    paths[url]['put'] = self.get_content(endpoint)
                elif endpoint.patch is not GenericAPI.patch:
                    paths[url]['patch'] = self.get_content(endpoint)
                elif endpoint.delete is not GenericAPI.delete:
                    paths[url]['delete'] = self.get_content(endpoint)

        openapi_content = {
            'openapi': '3.0.0',
            'paths': paths,
            'components': {}
        }
        print(f'{openapi_content=}')
        return TemplateResponse(name='openapi.html', context={'openapi_content': openapi_content})
