import types

from panther.app import GenericAPI
from panther.configs import config
from panther.response import TemplateResponse


class OpenAPI(GenericAPI):
    @classmethod
    def get_content(cls, method):
        return {
            'responses': {
                # TODO: 'responses': method.output_model.status_code,
                '200': {
                    'content': {
                        'application/json': {
                            'schema': method.output_model.schema() if method.output_model else {}
                        }
                    }
                }
            }
        }
    @classmethod
    def post_content(cls, method):
        return {
            'responses': {
                # TODO: 'responses': method.output_model.status_code,
                '200': {
                    'content': {
                        'application/json': {
                            'schema': method.output_model.schema() if method.output_model else {}
                        }
                    }
                }
            }
        }
    @classmethod
    def put_content(cls, method):
        return {
            'responses': {
                # TODO: 'responses': method.output_model.status_code,
                '200': {
                    'content': {
                        'application/json': {
                            'schema': method.output_model.schema() if method.output_model else {}
                        }
                    }
                }
            }
        }
    @classmethod
    def patch_content(cls, method):
        return {
            'responses': {
                # TODO: 'responses': method.output_model.status_code,
                '200': {
                    'content': {
                        'application/json': {
                            'schema': method.output_model.schema() if method.output_model else {}
                        }
                    }
                }
            }
        }
    @classmethod
    def delete_content(cls, method):
        return {
            'responses': {
                # TODO: 'responses': method.output_model.status_code,
                '204': {
                    'content': {
                        'application/json': {
                            'schema': method.output_model.schema() if method.output_model else {}
                        }
                    }
                }
            }
        }
    def get(self):
        paths = {}
        # TODO: Separate them with their modules
        #   Find the output_model or process the method with `ast`
        #   Find the input_model
        #   Find method in FunctionType, I currently we don't have access to `methods`
        #   Create Component for output_model and input_model s
        for url, method in config.FLAT_URLS.items():
            if url == '':
                url = '/'
            paths[url] = {}
            if not isinstance(method, types.FunctionType):
                if method.post is not GenericAPI.post:
                    paths[url]['post'] = self.post_content(method)
                elif method.get is not GenericAPI.get:
                    paths[url]['get'] = self.get_content(method)
                elif method.put is not GenericAPI.put:
                    paths[url]['put'] = self.put_content(method)
                elif method.patch is not GenericAPI.patch:
                    paths[url]['patch'] = self.patch_content(method)
                elif method.delete is not GenericAPI.delete:
                    paths[url]['delete'] = self.delete_content(method)
            else:
                methods = method.api_config['methods']

                if methods is None or 'POST' in methods:
                    paths[url]['post'] = self.post_content(method)
                if methods is None or 'GET' in methods:
                    paths[url]['get'] = self.get_content(method)
                if methods is None or 'PUT' in methods:
                    paths[url]['put'] = self.put_content(method)
                if methods is None or 'patch' in methods:
                    paths[url]['patch'] = self.patch_content(method)
                if methods is None or 'delete' in methods:
                    paths[url]['delete'] = self.delete_content(method)

        print(f'{paths=}')
        openapi_content = {
            'openapi': '3.0.0',
            'paths': paths,
            'components': {}
        }
        openapi_content_bak = {
            "openapi": "3.0.0",
            "paths": {
                "/example": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "message": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "ExampleSchema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer"
                            },
                            "name": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }

        return TemplateResponse(name='openapi.html', context={'openapi_content': openapi_content})