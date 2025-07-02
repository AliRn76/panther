from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel

from panther import Panther, status
from panther.app import API, GenericAPI
from panther.configs import config
from panther.db import Model
from panther.openapi.urls import url_routing
from panther.openapi.utils import EndpointParser
from panther.response import Response
from panther.test import APIClient


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
        assert parsed.response_data == True

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
