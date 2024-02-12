from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API
from panther.request import Request
from panther.test import APIClient


@API()
async def flat_multipart_api(request: Request):
    return request.data


@API()
async def single_file_multipart_api(request: Request):
    return {
        'file_name': request.data['file'].file_name,
        'content_type': request.data['file'].content_type,
        'file': request.data['file'].file.decode(),
    }


@API()
async def several_file_multipart_api(request: Request):
    return {
        'file1': {
            'file_name': request.data['file1'].file_name,
            'content_type': request.data['file1'].content_type,
            'file': request.data['file1'].file.decode(),
        },
        'file2': {
            'file_name': request.data['file2'].file_name,
            'content_type': request.data['file2'].content_type,
            'file': request.data['file2'].file.decode(),
        }
    }


@API()
async def complex_multipart_api(request: Request):
    return {
        'name': request.data['name'],
        'age': request.data['age'],
        'file1': {
            'file_name': request.data['file1'].file_name,
            'content_type': request.data['file1'].content_type,
            'file': request.data['file1'].file.decode(),
        },
        'file2': {
            'file_name': request.data['file2'].file_name,
            'content_type': request.data['file2'].content_type,
            'file': request.data['file2'].file.decode(),
        }
    }


urls = {
    'flat_multipart': flat_multipart_api,
    'single_file_multipart': single_file_multipart_api,
    'several_file_multipart': several_file_multipart_api,
    'complex_multipart': complex_multipart_api,
}


class TestMultipart(IsolatedAsyncioTestCase):
    CONTENT_TYPE = 'multipart/form-data; boundary=--------------------------201301649688174364392792'
    FLAT_PAYLOAD = (
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="name"\r\n\r\n'
            b'Ali Rn\r\n'
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="age"\r\n\r\n'
            b'25\r\n'
            b'----------------------------201301649688174364392792--\r\n'
        )
    SINGLE_FILE_PAYLOAD = (
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="file"; filename="hello_world.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Hello World\n\r\n'
            b'----------------------------201301649688174364392792--\r\n'
        )
    SEVERAL_FILE_PAYLOAD = (
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="file1"; filename="hello_world1.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Hello World1\n\r\n'
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="file2"; filename="hello_world2.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Hello World2\n\r\n'
            b'----------------------------201301649688174364392792--\r\n'
        )
    COMPLEX_PAYLOAD = (
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="name"\r\n\r\n'
            b'Ali Rn\r\n'
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="file1"; filename="hello_world1.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Hello World1\n\r\n'
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="file2"; filename="hello_world2.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Hello World2\n\r\n'
            b'----------------------------201301649688174364392792\r\n'
            b'Content-Disposition: form-data; name="age"\r\n\r\n'
            b'25\r\n'
            b'----------------------------201301649688174364392792--\r\n'
        )

    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    async def test_flat_multipart(self):
        res = await self.client.post(
            'flat_multipart',
            content_type=self.CONTENT_TYPE,
            payload=self.FLAT_PAYLOAD,
        )
        assert res.status_code == 200
        assert res.data == {'name': 'Ali Rn', 'age': '25'}

    async def test_single_file_multipart(self):
        res = await self.client.post(
            'single_file_multipart',
            content_type=self.CONTENT_TYPE,
            payload=self.SINGLE_FILE_PAYLOAD,
        )

        assert res.status_code == 200
        assert res.data == {
            'file_name': 'hello_world.txt',
            'content_type': 'text/plain',
            'file': 'Hello World\n',
        }

    async def test_several_file_multipart(self):
        res = await self.client.post(
            'several_file_multipart',
            content_type=self.CONTENT_TYPE,
            payload=self.SEVERAL_FILE_PAYLOAD,
        )

        assert res.status_code == 200
        assert res.data == {
            'file1': {
                'file_name': 'hello_world1.txt',
                'content_type': 'text/plain',
                'file': 'Hello World1\n',
            },
            'file2': {
                'file_name': 'hello_world2.txt',
                'content_type': 'text/plain',
                'file': 'Hello World2\n',
            }
        }

    async def test_complex_multipart(self):
        res = await self.client.post(
            'complex_multipart',
            content_type=self.CONTENT_TYPE,
            payload=self.COMPLEX_PAYLOAD,
        )

        assert res.status_code == 200
        assert res.data == {
            'name': 'Ali Rn',
            'age': '25',
            'file1': {
                'file_name': 'hello_world1.txt',
                'content_type': 'text/plain',
                'file': 'Hello World1\n',
            },
            'file2': {
                'file_name': 'hello_world2.txt',
                'content_type': 'text/plain',
                'file': 'Hello World2\n',
            }
        }
