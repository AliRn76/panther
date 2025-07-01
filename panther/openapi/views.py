from panther.app import GenericAPI
from panther.openapi.utils import OpenAPI
from panther.response import TemplateResponse


class ScalarOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='scalar.html', context={'openapi_content': OpenAPI.get_content()})

class SwaggerOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='swagger.html', context={'openapi_content': OpenAPI.get_content()})

class RedocOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='redoc.html', context={'openapi_content': OpenAPI.get_content()})

class RapiDocOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='rapidoc.html', context={'openapi_content': OpenAPI.get_content()})

class SpotlightOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='spotlight.html', context={'openapi_content': OpenAPI.get_content()})
