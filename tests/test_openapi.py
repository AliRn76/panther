from unittest import IsolatedAsyncioTestCase

from panther import Panther, status
from panther.app import API, GenericAPI
from panther.openapi.urls import urls
from panther.openapi.utils import ParseEndpoint
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


class TestPanelAPIs(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls={'swagger': urls})
        cls.client = APIClient(app=app)

    async def test_swagger(self):
        response = await self.client.get('/swagger/')
        expected_response = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swagger UI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.16.0/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.16.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>
    <script>
    const openapiContent = {"components": {}, "openapi": "3.0.0", "paths": {"/swagger/": {"get": {"responses": {"200": {"content": {"application/json": {"schema": {"properties": {}}}}}}, "summary": null, "tags": ["panther.openapi"], "title": "OpenAPI"}}}};

    const ui = SwaggerUIBundle({
        spec: openapiContent,
        dom_id: '#swagger-ui',
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
    });
    </script>
</body>
</html>"""
        assert expected_response == response.data

    async def test_my_api1(self):
        parsed = ParseEndpoint(my_api1, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api2(self):
        parsed = ParseEndpoint(my_api2, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api3(self):
        parsed = ParseEndpoint(my_api3, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api4(self):
        parsed = ParseEndpoint(my_api4, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api5(self):
        parsed = ParseEndpoint(my_api5, 'get')
        assert parsed.status_code == 201
        assert parsed.data == {}

    async def test_my_api6(self):
        parsed = ParseEndpoint(my_api6, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {}

    async def test_my_api7(self):
        parsed = ParseEndpoint(my_api7, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {}

    async def test_my_api8(self):
        parsed = ParseEndpoint(my_api8, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {}

    async def test_my_api9(self):
        parsed = ParseEndpoint(my_api9, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api10(self):
        parsed = ParseEndpoint(my_api10, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api11(self):
        parsed = ParseEndpoint(my_api11, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api12(self):
        parsed = ParseEndpoint(my_api12, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api13(self):
        parsed = ParseEndpoint(my_api13, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api14(self):
        parsed = ParseEndpoint(my_api14, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api15(self):
        parsed = ParseEndpoint(my_api15, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api16(self):
        parsed = ParseEndpoint(my_api16, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api17(self):
        parsed = ParseEndpoint(my_api17, 'get')
        assert parsed.status_code == 207
        assert parsed.data == {}

    async def test_my_api15_get(self):
        parsed = ParseEndpoint(API18, 'get')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api15_post(self):
        parsed = ParseEndpoint(API18, 'post')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api15_put(self):
        parsed = ParseEndpoint(API18, 'put')
        assert parsed.status_code == 200
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api15_patch(self):
        parsed = ParseEndpoint(API18, 'patch')
        assert parsed.status_code == 201
        assert parsed.data == {'detail': 'ok'}

    async def test_my_api15_delete(self):
        parsed = ParseEndpoint(API18, 'delete')
        assert parsed.status_code == 204
        assert parsed.data == {}
