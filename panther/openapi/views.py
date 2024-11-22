import types

from panther.app import GenericAPI
from panther.configs import config
from panther.response import TemplateResponse


class OpenAPI(GenericAPI):
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
            if not isinstance(method, types.FunctionType):
                if method.post is not GenericAPI.post:
                    paths[url] = {
                        'post': {
                            'responses': {
                                '200': {
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                "properties": {
                                                    "message": {
                                                        "type": "string"
                                                    }
                                                }
                                                # method.output_model.schema()['properties']
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                elif method.get is not GenericAPI.get:
                    paths[url] = {
                        'get': {}
                    }
                elif method.put is not GenericAPI.put:
                    paths[url] = {
                        'put': {}
                    }
                elif method.patch is not GenericAPI.patch:
                    paths[url] = {
                        'patch': {}
                    }
                elif method.delete is not GenericAPI.delete:
                    paths[url] = {
                        'delete': {}
                    }
            else:
                paths[url] = {
                    'post': {},
                    'get': {},
                    'put': {},
                    'patch': {},
                    'delete': {},
                }
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

        return TemplateResponse(path='openapi.html', context={'openapi_content': openapi_content})