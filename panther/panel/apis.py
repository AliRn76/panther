import contextlib

from panther import status
from panther.app import API
from panther.configs import config
from panther.db.connections import db
from panther.db.connections import redis
from panther.panel.utils import get_model_fields
from panther.request import Request
from panther.response import Response

with contextlib.suppress(ImportError):
    import pymongo
    from pymongo.errors import PyMongoError


@API(methods=['GET'])
async def models_api():
    return [{
        'name': model.__name__,
        'module': model.__module__,
        'index': i
    } for i, model in enumerate(config.MODELS)]


@API(methods=['GET', 'POST'])
async def documents_api(request: Request, index: int):
    model = config.MODELS[index]

    if request.method == 'POST':
        validated_data = API.validate_input(model=model, request=request)
        document = model.insert_one(**validated_data.model_dump(exclude=['id']))
        return Response(data=document, status_code=status.HTTP_201_CREATED)

    else:
        result = {
            'fields': get_model_fields(model),
        }
        if data := model.find():
            result['data'] = data
        else:
            result['data'] = []
        return result


@API(methods=['PUT', 'DELETE', 'GET'])
async def single_document_api(request: Request, index: int, document_id: int | str):
    model = config.MODELS[index]

    if document := model.find_one(id=document_id):
        if request.method == 'PUT':
            validated_data = API.validate_input(model=model, request=request)
            document.update(**validated_data.model_dump(exclude=['id']))
            return Response(data=document, status_code=status.HTTP_202_ACCEPTED)

        elif request.method == 'DELETE':
            document.delete()
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        else:  # GET
            return document

    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@API()
async def healthcheck_api():
    checks = []

    # Database
    if config.QUERY_ENGINE.__name__ == 'BaseMongoDBQuery':
        with pymongo.timeout(3):
            try:
                ping = db.session.command('ping').get('ok') == 1.0
                checks.append(ping)
            except PyMongoError:
                checks.append(False)
    # Redis
    if redis.is_connected:
        checks.append(await redis.ping())

    return Response(all(checks))
