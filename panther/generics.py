import logging

from panther import status
from panther.app import GenericAPI
from panther.db import Model
from panther.db.cursor import Cursor
from panther.exceptions import APIError
from panther.request import Request
from panther.response import Response

logger = logging.getLogger('panther')


class ObjectRequired:
    async def object(self, **kwargs) -> Model:
        """
        Return a single object
        `object` is used in RetrieveAPI, UpdateAPI, DeleteAPI
        """
        logger.error('`object()` method in not implemented.')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class ObjectsRequired:
    async def objects(self, **kwargs) -> list[Model] | Cursor:
        """
        Return list of objects
        `objects` is used in ListAPI
        """
        logger.error('`objects()` method in not implemented.')
        raise APIError(status_code=status.HTTP_501_NOT_IMPLEMENTED)


class RetrieveAPI(GenericAPI, ObjectRequired):
    async def get(self, request: Request, **kwargs):
        obj = await self.object(request=request, **kwargs)
        return Response(data=obj, status_code=status.HTTP_200_OK)


class ListAPI(GenericAPI, ObjectsRequired):
    async def get(self, request: Request, **kwargs):
        obj = await self.objects(request=request, **kwargs)
        return Response(data=obj, status_code=status.HTTP_200_OK)


class CreateAPI(GenericAPI):
    async def post(self, request: Request, **kwargs):
        obj = await request.validated_data.create()
        return Response(data=obj, status_code=status.HTTP_201_CREATED)


class UpdateAPI(GenericAPI, ObjectRequired):
    async def put(self, request: Request, **kwargs):
        obj = await self.object(request=request, **kwargs)
        await request.validated_data.update(obj)
        return Response(data=obj, status_code=status.HTTP_200_OK)

    async def patch(self, request: Request, **kwargs):
        obj = await self.object(request=request, **kwargs)
        await request.validated_data.partial_update(obj)
        return Response(data=obj, status_code=status.HTTP_200_OK)


class DeleteAPI(GenericAPI, ObjectRequired):
    async def delete(self, request: Request, **kwargs):
        obj = await self.object(request=request, **kwargs)
        await obj.delete()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
