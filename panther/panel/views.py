from panther import status

from panther.app import API, GenericAPI
from panther.configs import config
from panther.exceptions import RedirectAPIError
from panther.panel.utils import get_model_fields, get_models
from panther.permissions import BasePermission
from panther.request import Request
from panther.response import TemplateResponse, Response, Cookie


class AdminPanelPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        if 'cookie' in request.headers:
            return True
        raise RedirectAPIError(url='login')


class LoginView(GenericAPI):
    def get(self):
        return TemplateResponse(path='login.html', context={'tables': get_models()})

    def post(self, request: Request):
        return Response(
            status_code=status.HTTP_200_OK,
            set_cookies=[Cookie(key='token', value='this is token', max_age=120)]
        )


@API(methods=['GET'])
def home_page_view():
    return TemplateResponse(path='home.html', context={'tables': get_models()})


@API(methods=['GET'], permissions=[AdminPanelPermission])
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
