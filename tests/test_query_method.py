from datetime import timedelta
from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel

from panther import Panther
from panther.app import API, GenericAPI
from panther.caching import caches
from panther.configs import config
from panther.openapi.utils import OpenAPIGenerator
from panther.permissions import IsAuthenticatedOrReadonly
from panther.request import Request
from panther.response import Response
from panther.test import APIClient


class QueryInput(BaseModel):
    term: str
    limit: int = 10


@API(methods=['QUERY'], input_model=QueryInput)
async def function_query(request: Request):
    return {
        'method': request.method,
        'query': request.validated_data.model_dump(),
    }


class ClassQuery(GenericAPI):
    input_model = QueryInput

    async def query(self, request: Request):
        return {
            'method': request.method,
            'query': request.validated_data.model_dump(),
        }


@API(methods=['QUERY'])
async def sql_query(request: Request):
    return Response(
        data={'query': request.data.decode()},
        headers={'Accept-Query': 'application/sql, "application/jsonpath"'},
    )


@API(methods=['QUERY'], permissions=[IsAuthenticatedOrReadonly])
async def readonly_query():
    return {'detail': 'ok'}


query_cache_calls = 0


@API(methods=['QUERY'], cache=timedelta(minutes=1))
async def cached_query(request: Request):
    global query_cache_calls
    query_cache_calls += 1
    return {'call': query_cache_calls, 'query': request.data}


urls = {
    'function-query': function_query,
    'class-query': ClassQuery,
    'sql-query': sql_query,
    'readonly-query': readonly_query,
    'cached-query': cached_query,
}


class TestQueryMethod(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        caches.clear()
        config.refresh()

    async def test_function_query_with_validated_json_body(self):
        response = await self.client.query('function-query', payload={'term': 'panther', 'limit': 5})

        assert response.status_code == 200
        assert response.data == {
            'method': 'QUERY',
            'query': {'term': 'panther', 'limit': 5},
        }

    async def test_class_query_with_content_type_parameters(self):
        response = await self.client.query(
            'class-query',
            payload={'term': 'async'},
            content_type='application/json; charset=UTF-8',
        )

        assert response.status_code == 200
        assert response.data == {
            'method': 'QUERY',
            'query': {'term': 'async', 'limit': 10},
        }

    async def test_query_requires_content_type(self):
        response = await self.client.query(
            'function-query',
            payload={'term': 'panther'},
            content_type=None,
        )

        assert response.status_code == 400
        assert response.data == {'detail': 'Content-Type header is required for QUERY requests'}

    async def test_query_rejects_content_inconsistent_with_json(self):
        response = await self.client.query(
            'function-query',
            payload=b'not-json',
            content_type='application/json',
        )

        assert response.status_code == 400
        assert response.data == {'detail': 'Content-Type is inconsistent with the QUERY request content'}

    async def test_query_rejects_empty_json_content(self):
        response = await self.client.query(
            'function-query',
            payload=b'',
            content_type='application/json',
        )

        assert response.status_code == 400
        assert response.data == {'detail': 'Content-Type is inconsistent with the QUERY request content'}

    async def test_query_supports_application_defined_media_types(self):
        with self.assertLogs('panther', level='WARNING'):
            response = await self.client.query(
                'sql-query',
                payload=b'SELECT * FROM contacts',
                content_type='application/sql',
            )

        assert response.status_code == 200
        assert response.data == {'query': 'SELECT * FROM contacts'}
        assert response.headers['Accept-Query'] == 'application/sql, "application/jsonpath"'

    async def test_query_only_endpoints_return_allow_header(self):
        function_response = await self.client.get('function-query')
        class_response = await self.client.get('class-query')

        assert function_response.status_code == 405
        assert function_response.headers['Allow'] == 'QUERY'
        assert class_response.status_code == 405
        assert class_response.headers['Allow'] == 'QUERY'

    async def test_query_is_treated_as_readonly_by_builtin_permission(self):
        response = await self.client.query('readonly-query', payload={'term': 'panther'})

        assert response.status_code == 200
        assert response.data == {'detail': 'ok'}

    async def test_query_cache_key_includes_content_and_metadata(self):
        global query_cache_calls
        query_cache_calls = 0
        caches.clear()

        first = await self.client.query('cached-query', payload={'term': 'one'})
        repeated = await self.client.query('cached-query', payload={'term': 'one'})
        different_content = await self.client.query('cached-query', payload={'term': 'two'})
        different_content_type = await self.client.query(
            'cached-query',
            payload={'term': 'one'},
            content_type='application/json; charset=UTF-8',
        )

        assert first.data == repeated.data
        assert first.data['call'] == 1
        assert different_content.data['call'] == 2
        assert different_content_type.data['call'] == 3

    def test_openapi_32_documents_query_operations(self):
        specification = OpenAPIGenerator.generate_openapi_spec()

        assert specification['openapi'] == '3.2.0'
        function_operation = specification['paths']['/function-query/']['query']
        class_operation = specification['paths']['/class-query/']['query']
        assert function_operation['requestBody']['required'] is True
        assert class_operation['requestBody']['required'] is True
        assert function_operation['requestBody']['content']['application/json']['schema'] == {
            '$ref': '#/components/schemas/QueryInput',
        }
