from panther import status

from panther.app import API, GenericAPI
from panther.configs import config
from panther.panel.utils import get_model_fields, get_models
from panther.request import Request
from panther.response import TemplateResponse, Response, Cookie


class LoginView(GenericAPI):
    def get(self):
        return TemplateResponse(path='login.html', context={'tables': get_models()})

    def post(self, request: Request):
        return Response(status_code=status.HTTP_200_OK, set_cookies=[Cookie(key='token', value='this is token')])


@API(methods=['GET'])
def home_page_view():
    return TemplateResponse(path='home.html', context={'tables': get_models()})


@API(methods=['GET'], auth=True)
async def table_view(index: int):
    model = config.MODELS[index]
    if data := await model.find():
        data = data
    else:
        data = []

    return TemplateResponse(
        path='table.html',
        context={
            'table': model.__name__,
            'fields': get_model_fields(model),
            'tables': get_models(),
            'records': Response.prepare_data(data),
        }
    )
