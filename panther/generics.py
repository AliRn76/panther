import contextlib
import logging

from pantherdb import Cursor as PantherDBCursor

from panther import status
from panther.app import GenericAPI
from panther.configs import config
from panther.db import Model
from panther.db.cursor import Cursor
from panther.exceptions import APIError
from panther.pagination import Pagination
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

with contextlib.suppress(ImportError):
    # Only required if user wants to use mongodb
    import bson

logger = logging.getLogger('panther')


class ObjectRequired:
    def _check_object(self, instance):
        if instance and issubclass(type(instance), Model) is False:
            logger.critical(f'`{self.__class__.__name__}.object()` should return instance of a Model --> `find_one()`')
            raise APIError

    async def object(self, request: Request, **kwargs):
        """
        Used in `RetrieveAPI`, `UpdateAPI`, `DeleteAPI`
        """
        logger.error(f'`object()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class CursorRequired:
    def _check_cursor(self, cursor):
        if isinstance(cursor, (Cursor, PantherDBCursor)) is False:
            logger.critical(f'`{self.__class__.__name__}.cursor()` should return a Cursor --> `find()`')
            raise APIError

    async def cursor(self, request: Request, **kwargs) -> Cursor | PantherDBCursor:
        """
        Used in `ListAPI`
        Should return `.find()`
        """
        logger.error(f'`cursor()` method is not implemented in {self.__class__} .')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class RetrieveAPI(GenericAPI, ObjectRequired):
    async def get(self, request: Request, **kwargs):
        instance = await self.object(request=request, **kwargs)
        self._check_object(instance)

        return Response(data=instance, status_code=status.HTTP_200_OK)


class ListAPI(GenericAPI, CursorRequired):
    sort_fields: list[str]
    search_fields: list[str]
    filter_fields: list[str]
    pagination: type[Pagination]

    async def get(self, request: Request, **kwargs):
        cursor, pagination = await self.prepare_cursor(request=request, **kwargs)
        return Response(data=cursor, pagination=pagination, status_code=status.HTTP_200_OK)

    async def prepare_cursor(self, request: Request, **kwargs) -> tuple[Cursor | PantherDBCursor, Pagination | None]:
        cursor = await self.cursor(request=request, **kwargs)
        self._check_cursor(cursor)

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
        if hasattr(self, 'filter_fields'):
            for field in self.filter_fields:
                if field in query_params:
                    if config.DATABASE.__class__.__name__ == 'MongoDBConnection':
                        with contextlib.suppress(Exception):
                            # Change type of the value if it is ObjectId
                            if cursor.cls.model_fields[field].metadata[0].func.__name__ == 'validate_object_id':
                                _filter[field] = bson.ObjectId(query_params[field])
                                continue
                    _filter[field] = query_params[field]
        return _filter

    def process_search(self, query_params: dict) -> dict:
        if hasattr(self, 'search_fields') and 'search' in query_params:
            value = query_params['search']
            if config.DATABASE.__class__.__name__ == 'MongoDBConnection':
                if search := [{field: {'$regex': value}} for field in self.search_fields]:
                    return {'$or': search}
            else:
                logger.warning(f'`?search={value} does not work well while using `PantherDB` as Database')
                return {field: value for field in self.search_fields}
        return {}

    def process_sort(self, query_params: dict) -> list:
        if hasattr(self, 'sort_fields') and 'sort' in query_params:
            return [
                (field, -1 if param[0] == '-' else 1)
                for field in self.sort_fields for param in query_params['sort'].split(',')
                if field == param.removeprefix('-')
            ]

    def process_pagination(self, query_params: dict, cursor: Cursor | PantherDBCursor) -> Pagination | None:
        if hasattr(self, 'pagination'):
            return self.pagination(query_params=query_params, cursor=cursor)


class CreateAPI(GenericAPI):
    input_model: type[ModelSerializer]

    async def post(self, request: Request, **kwargs):
        instance = await request.validated_data.create(validated_data={
            field: getattr(request.validated_data, field)
            for field in request.validated_data.model_fields_set
            if field != 'request'
        })
        return Response(data=instance, status_code=status.HTTP_201_CREATED)


class UpdateAPI(GenericAPI, ObjectRequired):
    input_model: type[ModelSerializer]

    async def put(self, request: Request, **kwargs):
        instance = await self.object(request=request, **kwargs)
        self._check_object(instance)

        await request.validated_data.update(
            instance=instance,
            validated_data=request.validated_data.model_dump()
        )
        return Response(data=instance, status_code=status.HTTP_200_OK)

    async def patch(self, request: Request, **kwargs):
        instance = await self.object(request=request, **kwargs)
        self._check_object(instance)

        await request.validated_data.partial_update(
            instance=instance,
            validated_data=request.validated_data.model_dump(exclude_none=True)
        )
        return Response(data=instance, status_code=status.HTTP_200_OK)


class DeleteAPI(GenericAPI, ObjectRequired):
    async def pre_delete(self, instance, request: Request, **kwargs):
        pass

    async def post_delete(self, instance, request: Request, **kwargs):
        pass

    async def delete(self, request: Request, **kwargs):
        instance = await self.object(request=request, **kwargs)
        self._check_object(instance)

        await self.pre_delete(instance, request=request, **kwargs)
        await instance.delete()
        await self.post_delete(instance, request=request, **kwargs)

        return Response(status_code=status.HTTP_204_NO_CONTENT)


class ListCreateAPI(CreateAPI, ListAPI):
    pass


class UpdateDeleteAPI(UpdateAPI, DeleteAPI):
    pass


class RetrieveUpdateDeleteAPI(RetrieveAPI, UpdateAPI, DeleteAPI):
    pass
