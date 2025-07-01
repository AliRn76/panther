from panther.app import GenericAPI
from panther.openapi.utils import OpenAPI
from panther.response import TemplateResponse


class SwaggerOpenAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name='swagger.html', context={'openapi_content': OpenAPI.get_content()})
