from panther.app import GenericAPI
from panther.openapi import OutputSchema
from panther.openapi.utils import OpenAPIGenerator
from panther.response import TemplateResponse


class ScalarOpenAPI(GenericAPI):
    output_schema = OutputSchema(exclude_in_docs=True)

    def get(self):
        return TemplateResponse(name='scalar.html', context={'openapi': OpenAPIGenerator.generate_openapi_spec()})


class SwaggerOpenAPI(GenericAPI):
    output_schema = OutputSchema(exclude_in_docs=True)

    def get(self):
        return TemplateResponse(name='swagger.html', context={'openapi': OpenAPIGenerator.generate_openapi_spec()})


class RedocOpenAPI(GenericAPI):
    output_schema = OutputSchema(exclude_in_docs=True)

    def get(self):
        return TemplateResponse(name='redoc.html', context={'openapi': OpenAPIGenerator.generate_openapi_spec()})


class RapiDocOpenAPI(GenericAPI):
    output_schema = OutputSchema(exclude_in_docs=True)

    def get(self):
        return TemplateResponse(name='rapidoc.html', context={'openapi': OpenAPIGenerator.generate_openapi_spec()})


class SpotlightOpenAPI(GenericAPI):
    output_schema = OutputSchema(exclude_in_docs=True)

    def get(self):
        return TemplateResponse(name='spotlight.html', context={'openapi': OpenAPIGenerator.generate_openapi_spec()})
