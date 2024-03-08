import logging

import pymongo

from panther import status
from panther.app import GenericAPI
from panther.db import Model
from panther.db.cursor import Cursor
from panther.exceptions import APIError
from panther.request import Request
from panther.response import Response

logger = logging.getLogger('panther')


class ObjectRequired:
    async def object(self, request: Request, **kwargs) -> Model:
        """
        Used in `RetrieveAPI`, `UpdateAPI`, `DeleteAPI`
        """
        logger.error('`object()` method in not implemented.')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class ObjectsRequired:
    async def objects(self, request: Request, **kwargs) -> list[Model] | Cursor:
        """
        Used in `ListAPI`
        """
        logger.error('`objects()` method in not implemented.')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class RetrieveAPI(GenericAPI, ObjectRequired):
    async def get(self, request: Request, **kwargs):
        obj = await self.object(request=request, **kwargs)
        return Response(data=obj, status_code=status.HTTP_200_OK)


class ListAPI(GenericAPI, ObjectsRequired):
    sort_fields: list
    search_fields: list
    filter_fields: list

    def process_filters(self, query_params: dict) -> dict:
        if hasattr(self, 'filter_fields'):
            return {field: query_params[field] for field in self.filter_fields if field in query_params}

    def process_sort(self, query_params: dict) -> list:
        if hasattr(self, 'sort_fields') and 'sort' in query_params:
            return [
                (field, -1 if param[0] == '-' else 1)
                for field in self.sort_fields for param in query_params['sort'].split(',')
                if field == param.removeprefix('-')
            ]

    def process_search(self, query_params: dict) -> dict:
        if hasattr(self, 'search_fields') and 'search' in query_params:
            value = query_params['search']
            if search := [{field: {'$regex': value}} for field in self.search_fields]:
                return {'$or': search}
        return {}

    async def get(self, request: Request, **kwargs):
        objects = await self.objects(request=request, **kwargs)
        query = {}
        query |= self.process_filters(query_params=request.query_params)
        query |= self.process_search(query_params=request.query_params)

        if query:
            objects = await objects.cls.find(objects.filter | query)

        if sort := self.process_sort(query_params=request.query_params):
            objects = objects.sort(sort)

        return Response(data=objects, status_code=status.HTTP_200_OK)


class CreateAPI(GenericAPI):
    async def post(self, request: Request, **kwargs):
        request.validated_data.request = request
        instance = await request.validated_data.create(
            validated_data=request.validated_data.model_dump()
        )
        return Response(data=instance, status_code=status.HTTP_201_CREATED)


class UpdateAPI(GenericAPI, ObjectRequired):
    async def put(self, request: Request, **kwargs):
        request.validated_data.request = request
        instance = await self.object(request=request, **kwargs)
        await request.validated_data.update(
            instance=instance,
            validated_data=request.validated_data.model_dump()
        )
        return Response(data=instance, status_code=status.HTTP_200_OK)

    async def patch(self, request: Request, **kwargs):
        request.validated_data.request = request
        instance = await self.object(request=request, **kwargs)
        await request.validated_data.partial_update(
            instance=instance,
            validated_data=request.validated_data.model_dump(exclude_none=True)
        )
        return Response(data=instance, status_code=status.HTTP_200_OK)


class DeleteAPI(GenericAPI, ObjectRequired):
    async def delete(self, request: Request, **kwargs):
        instance = await self.object(request=request, **kwargs)
        await instance.delete()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
