import contextlib
import logging
from abc import abstractmethod

from pantherdb import Cursor as PantherDBCursor

from panther import status
from panther.app import GenericAPI
from panther.configs import config
from panther.db import Model
from panther.db.connections import MongoDBConnection
from panther.db.cursor import Cursor
from panther.db.models import ID
from panther.exceptions import APIError
from panther.pagination import Pagination
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

with contextlib.suppress(ImportError):
    # Only required if user wants to use mongodb
    import bson

logger = logging.getLogger('panther')


class RetrieveAPI(GenericAPI):
    @abstractmethod
    async def get_instance(self, request: Request, **kwargs) -> Model:
        """
        Should return an instance of Model, e.g. `await User.find_one()`
        """
        logger.error(f'`get_instance()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    async def get(self, request: Request, **kwargs):
        instance = await self.get_instance(request=request, **kwargs)
        return Response(data=instance, status_code=status.HTTP_200_OK)


class ListAPI(GenericAPI):
    sort_fields: list[str] = []
    search_fields: list[str] = []
    filter_fields: list[str] = []
    pagination: type[Pagination] | None = None

    @abstractmethod
    async def get_query(self, request: Request, **kwargs):
        """
        Should return a Cursor, e.g. `await User.find()`
        """
        logger.error(f'`get_query()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    async def get(self, request: Request, **kwargs):
        cursor, pagination = await self.prepare_cursor(request=request, **kwargs)
        return Response(data=cursor, pagination=pagination, status_code=status.HTTP_200_OK)

    async def prepare_cursor(self, request: Request, **kwargs) -> tuple[Cursor | PantherDBCursor, Pagination | None]:
        cursor = await self.get_query(request=request, **kwargs)
        if not isinstance(cursor, (Cursor, PantherDBCursor)):
            logger.error(f'`{self.__class__.__name__}.get_query()` should return a Cursor, e.g. `await Model.find()`')
            raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)

        query = {}
        query |= self.process_filters(query_params=request.query_params, cursor=cursor)
        query |= self.process_search(query_params=request.query_params)

        if query:
            cursor = await cursor.cls.find(cursor.filter | query)

        if sort := self.process_sort(query_params=request.query_params):
            cursor = cursor.sort(sort)

        if pagination := self.process_pagination(query_params=request.query_params, cursor=cursor):
            cursor = pagination.paginate()

        return cursor, pagination

    def process_filters(self, query_params: dict, cursor: Cursor | PantherDBCursor) -> dict:
        _filter = {}
        for field in self.filter_fields:
            if field in query_params:
                _filter[field] = query_params[field]
                if isinstance(config.DATABASE, MongoDBConnection) and cursor.cls.model_fields[field].annotation == ID:
                    _filter[field] = bson.ObjectId(_filter[field])
        return _filter

    def process_search(self, query_params: dict) -> dict:
        search_param = query_params.get('search')
        if not self.search_fields or not search_param:
            return {}
        if isinstance(config.DATABASE, MongoDBConnection):
            if search := [{field: {'$regex': search_param}} for field in self.search_fields]:
                return {'$or': search}
        return {field: search_param for field in self.search_fields}

    def process_sort(self, query_params: dict) -> list:
        sort_param = query_params.get('sort')
        if not self.sort_fields or not sort_param:
            return []
        return [
            (field, -1 if param.startswith('-') else 1)
            for param in sort_param.split(',')
            for field in self.sort_fields
            if field == param.removeprefix('-')
        ]

    def process_pagination(self, query_params: dict, cursor: Cursor | PantherDBCursor) -> Pagination | None:
        if self.pagination:
            return self.pagination(query_params=query_params, cursor=cursor)


class CreateAPI(GenericAPI):
    async def post(self, request: Request, **kwargs):
        instance = await request.validated_data.model.insert_one(request.validated_data.model_dump())
        return Response(data=instance, status_code=status.HTTP_201_CREATED)


class UpdateAPI(GenericAPI):
    @abstractmethod
    async def get_instance(self, request: Request, **kwargs) -> Model:
        """
        Should return an instance of Model, e.g. `await User.find_one()`
        """
        logger.error(f'`get_instance()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    async def put(self, request: Request, **kwargs):
        instance = await self.get_instance(request=request, **kwargs)
        await instance.update(request.validated_data.model_dump())
        return Response(data=instance, status_code=status.HTTP_200_OK)

    async def patch(self, request: Request, **kwargs):
        instance = await self.get_instance(request=request, **kwargs)
        await instance.update(request.validated_data.model_dump(exclude_none=True))
        return Response(data=instance, status_code=status.HTTP_200_OK)


class DeleteAPI(GenericAPI):
    @abstractmethod
    async def get_instance(self, request: Request, **kwargs) -> Model:
        """
        Should return an instance of Model, e.g. `await User.find_one()`
        """
        logger.error(f'`get_instance()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    async def pre_delete(self, instance, request: Request, **kwargs):
        """Hook for logic before deletion."""
        pass

    async def post_delete(self, instance, request: Request, **kwargs):
        """Hook for logic after deletion."""
        pass

    async def delete(self, request: Request, **kwargs):
        instance = await self.get_instance(request=request, **kwargs)
        await self.pre_delete(instance, request=request, **kwargs)
        await instance.delete()
        await self.post_delete(instance, request=request, **kwargs)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
