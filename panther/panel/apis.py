from panther import status
from panther.app import API
from panther.configs import config
from panther.panel.utils import get_model_fields
from panther.request import Request
from panther.response import Response


@API()
async def models_api():
    result = list()
    for i, m in enumerate(config['models']):
        data = dict()
        data['name'] = m['name']
        data['app'] = '.'.join(a for a in m['app'])
        data['path'] = m['path']
        data['index'] = i
        result.append(data)
    return result


@API()
async def documents_api(request: Request, index: int):
    model = config['models'][index]['class']

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


@API()
async def single_document_api(request: Request, index: int, document_id: int | str):
    model = config['models'][index]['class']

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

