from datetime import timedelta
from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel, Field

from panther import Panther, status
from panther.app import API, GenericAPI
from panther.configs import config
from panther.db import Model
from panther.middlewares.base import HTTPMiddleware
from panther.openapi import OutputSchema
from panther.openapi.urls import url_routing
from panther.openapi.utils import EndpointParser, OpenAPIGenerator
from panther.response import Response
from panther.test import APIClient
from panther.throttling import Throttle


@API()
def my_api1():
    return {'detail': 'ok'}


@API()
def my_api2():
    data = {'detail': 'ok'}
    return data


@API()
def my_api3():
    my_data = {'detail': 'ok'}
    return Response(data=my_data)


@API()
async def my_api4():
    return Response(data={'detail': 'ok'})


@API()
async def my_api5():
    return Response(status_code=201)


@API()
async def my_api6():
    return Response(status_code=status.HTTP_207_MULTI_STATUS)


@API()
def my_api7():
    my_status = status.HTTP_207_MULTI_STATUS
    return Response(status_code=my_status)


@API()
def my_api8():
    my_status = 207
    return Response(status_code=my_status)


@API()
def my_api9():
    return Response({'detail': 'ok'})


@API()
def my_api10():
    my_data = {'detail': 'ok'}
    return Response(my_data)


@API()
def my_api11():
    my_data = {'detail': 'ok'}
    return Response(my_data, status_code=207)


@API()
def my_api12():
    my_data = {'detail': 'ok'}
    return Response(my_data, status_code=status.HTTP_207_MULTI_STATUS)


@API()
def my_api13():
    my_data = {'detail': 'ok'}
    my_status = 207
    return Response(my_data, status_code=my_status)


@API()
def my_api14():
    my_data = {'detail': 'ok'}
    my_status = status.HTTP_207_MULTI_STATUS
    return Response(my_data, status_code=my_status)


@API()
def my_api15():
    my_data = {'detail': 'ok'}
    my_status = status.HTTP_207_MULTI_STATUS
    return Response(my_data, my_status)


@API()
def my_api16():
    my_data = {'detail': 'ok'}
    return Response(my_data, status.HTTP_207_MULTI_STATUS)


@API()
def my_api17():
    return Response({}, 207)


class API18(GenericAPI):
    def get(self, *args, **kwargs):
        return {'detail': 'ok'}

    def post(self, *args, **kwargs):
        my_data = {'detail': 'ok'}
        return my_data

    async def put(self, *args, **kwargs):
        my_data = {'detail': 'ok'}
        return Response(data=my_data)

    def patch(self, *args, **kwargs):
        my_data = {'detail': 'ok'}
        return Response(data=my_data, status_code=201)

    def delete(self, *args, **kwargs):
        return Response({}, status.HTTP_204_NO_CONTENT)


@API()
def my_api19():
    my_response = ['1', '2']
    return my_response


@API()
def my_api20():
    my_response = 'Hello World!'
    return my_response


@API()
def my_api21():
    my_response = True
    return my_response


@API()
def my_api22():
    my_response = (6, 9)
    return my_response


@API()
def my_api23():
    my_response = Response(data={'detail': 'Hello'}, status_code=207)
    return my_response


class CustomBaseModel(BaseModel):
    name: str
    children: list[str] | None = None


@API()
def my_api24():
    my_response = CustomBaseModel(name='Ali', children=['A', 'B', 'C'])
    return my_response


class CustomModel(Model):
    title: str


@API()
def my_api25():
    my_response = CustomModel(title='Book')
    return my_response


@API()
def my_api26():
    return CustomBaseModel(name='Ali')


@API()
def my_api27():
    return CustomModel(title='Book')


class DocumentInput(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    page_count: int = Field(gt=0)


class DocumentOutput(BaseModel):
    id: int
    title: str


class DocumentPermission:
    async def __call__(self, request):
        return True


class DocumentAuthentication:
    async def __call__(self, request):
        return None


class DocumentMiddleware(HTTPMiddleware):
    pass


@API(
    methods=['POST'],
    input_model=DocumentInput,
    output_schema=OutputSchema(
        model=DocumentOutput,
        status_code=status.HTTP_201_CREATED,
        tags=['documents'],
        deprecated=True,
    ),
    auth=DocumentAuthentication,
    permissions=[DocumentPermission],
    throttling=Throttle(rate=10, duration=timedelta(minutes=1)),
    cache=timedelta(minutes=5),
    middlewares=[DocumentMiddleware],
)
def create_document(document_id: int, preview: bool, scale: float, missing: str):
    """Create a document.

    Persists a document after validating its request body.
    """
    return Response({'id': document_id, 'title': 'Panther'}, status_code=status.HTTP_201_CREATED)


class DocumentDetailAPI(GenericAPI):
    output_model = DocumentOutput

    async def get(self, document_id: int):
        """Fetch a document."""
        return {'id': document_id, 'title': 'Panther'}


@API(output_schema=OutputSchema(exclude_in_docs=True))
def internal_document():
    return {'detail': 'internal'}


openapi_urls = {
    'documents/<document_id>/<preview>/<scale>/<missing>/': create_document,
    'documents/<document_id>/': DocumentDetailAPI,
    'internal-documents/': internal_document,
}


class TestOpenAPI(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls={'docs': url_routing})
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        config.refresh()

    # TODO: Uncomment and improve it at end of this pr

    async def test_swagger(self):
        response = await self.client.get('/docs/swagger/')
        expected_response = """<!doctype html>
<html>
  <head>
    <title>Swagger UI</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      SwaggerUIBundle({ spec: {"components": {"schemas": {}, "securitySchemes": {"BearerAuth": {"bearerFormat": "JWT", "scheme": "bearer", "type": "http"}}}, "info": {"description": "Auto-generated OpenAPI documentation for Panther project.", "title": "Panther API", "version": "1.0.0"}, "openapi": "3.0.0", "paths": {"/docs/rapidoc/": {}, "/docs/redoc/": {}, "/docs/scalar/": {}, "/docs/spotlight/": {}, "/docs/swagger/": {}}, "security": [{"BearerAuth": []}]}, dom_id: '#swagger-ui' });
    </script>
  </body>
</html>"""
        assert expected_response == response.data

    async def test_scalar(self):
        response = await self.client.get('/docs/scalar/')
        expected_response = """<!doctype html>
<html>
  <head>
    <title>Scalar API Reference</title>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <div id="app"></div>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    <script>
      Scalar.createApiReference('#app', {
        content: {"components": {"schemas": {}, "securitySchemes": {"BearerAuth": {"bearerFormat": "JWT", "scheme": "bearer", "type": "http"}}}, "info": {"description": "Auto-generated OpenAPI documentation for Panther project.", "title": "Panther API", "version": "1.0.0"}, "openapi": "3.0.0", "paths": {"/docs/rapidoc/": {}, "/docs/redoc/": {}, "/docs/scalar/": {}, "/docs/spotlight/": {}, "/docs/swagger/": {}}, "security": [{"BearerAuth": []}]}
      })
    </script>
  </body>
</html>"""
        assert expected_response == response.data

    async def test_redoc(self):
        response = await self.client.get('/docs/redoc/')
        expected_response = """<!doctype html>
<html>
  <head>
    <title>ReDoc API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <div id="redoc-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
    <script>
      Redoc.init({"components": {"schemas": {}, "securitySchemes": {"BearerAuth": {"bearerFormat": "JWT", "scheme": "bearer", "type": "http"}}}, "info": {"description": "Auto-generated OpenAPI documentation for Panther project.", "title": "Panther API", "version": "1.0.0"}, "openapi": "3.0.0", "paths": {"/docs/rapidoc/": {}, "/docs/redoc/": {}, "/docs/scalar/": {}, "/docs/spotlight/": {}, "/docs/swagger/": {}}, "security": [{"BearerAuth": []}]}, {}, document.getElementById("redoc-container"));
    </script>
  </body>
</html>"""
        assert expected_response == response.data

    async def test_rapidoc(self):
        response = await self.client.get('/docs/rapidoc/')
        expected_response = """<!doctype html>
<html>
  <head>
    <title>RapiDoc Inline JSON</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, minimum-scale=1, initial-scale=1, user-scalable=yes">
    <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
  </head>
  <body>
    <rapi-doc id="thedoc"
      render-style = "read"
      allow-try="false"
      allow-authentication = "false"
    > </rapi-doc>
    <script>
      document.addEventListener('readystatechange', (event) => {
        let docEl = document.getElementById("thedoc");
        docEl.loadSpec({"components": {"schemas": {}, "securitySchemes": {"BearerAuth": {"bearerFormat": "JWT", "scheme": "bearer", "type": "http"}}}, "info": {"description": "Auto-generated OpenAPI documentation for Panther project.", "title": "Panther API", "version": "1.0.0"}, "openapi": "3.0.0", "paths": {"/docs/rapidoc/": {}, "/docs/redoc/": {}, "/docs/scalar/": {}, "/docs/spotlight/": {}, "/docs/swagger/": {}}, "security": [{"BearerAuth": []}]});
      })
    </script>
  </body>
</html>"""
        assert expected_response == response.data

    async def test_spotlight(self):
        response = await self.client.get('/docs/spotlight/')
        expected_response = """<!doctype html>
<html>
<head>
  <title>Stoplight Elements with CSS</title>
  <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css" />
  <script type="module" src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
  <style>
    body, html {
      margin: 0; padding: 0; height: 100%;
    }
    elements-api {
      display: block;
      height: 100vh;
    }
  </style>
</head>
<body>
  <elements-api id="api-viewer" router="hash"></elements-api>
  <script>
    customElements.whenDefined("elements-api").then(() => {
      document.getElementById("api-viewer").apiDescriptionDocument = {"components": {"schemas": {}, "securitySchemes": {"BearerAuth": {"bearerFormat": "JWT", "scheme": "bearer", "type": "http"}}}, "info": {"description": "Auto-generated OpenAPI documentation for Panther project.", "title": "Panther API", "version": "1.0.0"}, "openapi": "3.0.0", "paths": {"/docs/rapidoc/": {}, "/docs/redoc/": {}, "/docs/scalar/": {}, "/docs/spotlight/": {}, "/docs/swagger/": {}}, "security": [{"BearerAuth": []}]};
    });
  </script>
</body>
</html>"""
        assert expected_response == response.data

    async def test_my_api1(self):
        parsed = EndpointParser(my_api1, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api2(self):
        parsed = EndpointParser(my_api2, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api3(self):
        parsed = EndpointParser(my_api3, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api4(self):
        parsed = EndpointParser(my_api4, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api5(self):
        parsed = EndpointParser(my_api5, 'get')
        assert parsed.status_code == 201
        assert parsed.response_data == {}

    async def test_my_api6(self):
        parsed = EndpointParser(my_api6, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {}

    async def test_my_api7(self):
        parsed = EndpointParser(my_api7, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {}

    async def test_my_api8(self):
        parsed = EndpointParser(my_api8, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {}

    async def test_my_api9(self):
        parsed = EndpointParser(my_api9, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api10(self):
        parsed = EndpointParser(my_api10, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api11(self):
        parsed = EndpointParser(my_api11, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api12(self):
        parsed = EndpointParser(my_api12, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api13(self):
        parsed = EndpointParser(my_api13, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api14(self):
        parsed = EndpointParser(my_api14, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api15(self):
        parsed = EndpointParser(my_api15, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api16(self):
        parsed = EndpointParser(my_api16, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api17(self):
        parsed = EndpointParser(my_api17, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {}

    async def test_my_api18_get(self):
        parsed = EndpointParser(API18, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api18_post(self):
        parsed = EndpointParser(API18, 'post')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api18_put(self):
        parsed = EndpointParser(API18, 'put')
        assert parsed.status_code == 200
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api18_patch(self):
        parsed = EndpointParser(API18, 'patch')
        assert parsed.status_code == 201
        assert parsed.response_data == {'detail': 'ok'}

    async def test_my_api18_delete(self):
        parsed = EndpointParser(API18, 'delete')
        assert parsed.status_code == 204
        assert parsed.response_data == {}

    async def test_my_api19(self):
        parsed = EndpointParser(my_api19, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == ['1', '2']

    async def test_my_api20(self):
        parsed = EndpointParser(my_api20, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == 'Hello World!'

    async def test_my_api21(self):
        parsed = EndpointParser(my_api21, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data is True

    async def test_my_api22(self):
        parsed = EndpointParser(my_api22, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == [6, 9]

    async def test_my_api23(self):
        parsed = EndpointParser(my_api23, 'get')
        assert parsed.status_code == 207
        assert parsed.response_data == {'detail': 'Hello'}

    async def test_my_api24(self):
        parsed = EndpointParser(my_api24, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'name': 'Ali', 'children': ['A', 'B', 'C']}

    async def test_my_api25(self):
        parsed = EndpointParser(my_api25, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'title': 'Book'}

    async def test_my_api26(self):
        parsed = EndpointParser(my_api26, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'name': 'Ali'}

    async def test_my_api27(self):
        parsed = EndpointParser(my_api27, 'get')
        assert parsed.status_code == 200
        assert parsed.response_data == {'title': 'Book'}


class TestOpenAPIGenerator(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Panther(__name__, configs=__name__, urls=openapi_urls)

    @classmethod
    def tearDownClass(cls) -> None:
        config.refresh()

    async def test_generates_complete_contract_for_documented_endpoints(self):
        spec = OpenAPIGenerator.generate_openapi_spec()

        create_operation = spec['paths']['/documents/{document_id}/{preview}/{scale}/{missing}/']['post']
        assert create_operation['operationId'] == 'create_document_post'
        assert create_operation['summary'] == 'Create a document.'
        assert create_operation['description'] == (
            "Persists a document after validating its request body.<br>  - Permissions: ['DocumentPermission']"
            '<br>  - Throttling: 10 per 0:01:00<br>  - Cache: 0:05:00'
            "<br>  - Middlewares: ['DocumentMiddleware']"
        )
        assert create_operation['tags'] == ['documents']
        assert create_operation['security'] == [{'BearerAuth': []}]
        assert create_operation['deprecated'] is True
        assert create_operation['parameters'] == [
            {'name': 'document_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
            {'name': 'preview', 'in': 'path', 'required': True, 'schema': {'type': 'boolean'}},
            {'name': 'scale', 'in': 'path', 'required': True, 'schema': {'type': 'number'}},
            {'name': 'missing', 'in': 'path', 'required': True, 'schema': {'type': 'string'}},
        ]
        assert create_operation['requestBody'] == {
            'required': True,
            'content': {'application/json': {'schema': {'$ref': '#/components/schemas/DocumentInput'}}},
        }
        assert create_operation['responses'] == {
            201: {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/DocumentOutput'}}}},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden'},
            400: {'description': 'Bad Request'},
            422: {'description': 'Unprocessable Entity'},
        }

        detail_operation = spec['paths']['/documents/{document_id}/']['get']
        assert detail_operation['parameters'] == [
            {'name': 'document_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
        ]
        assert 'requestBody' not in detail_operation
        assert detail_operation['responses'] == {
            200: {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/DocumentOutput'}}}},
        }

        assert spec['paths']['/internal-documents/'] == {}
        assert set(spec['components']['schemas']) == {'DocumentInput', 'DocumentOutput'}
        assert spec['components']['schemas']['DocumentInput']['properties']['title']['minLength'] == 3
        assert spec['components']['schemas']['DocumentInput']['properties']['title']['maxLength'] == 100
        assert spec['components']['schemas']['DocumentInput']['properties']['page_count']['exclusiveMinimum'] == 0
