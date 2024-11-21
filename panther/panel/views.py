from panther import status
from panther.app import API, GenericAPI
from panther.configs import config
from panther.db.models import BaseUser
from panther.exceptions import RedirectAPIError, AuthenticationAPIError
from panther.panel.utils import get_model_fields, get_models
from panther.permissions import BasePermission
from panther.request import Request
from panther.response import TemplateResponse, Response, Cookie, RedirectResponse


class AdminPanelPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        if 'cookie' in request.headers:
            return True
        raise RedirectAPIError(url=f'login?redirect_to={request.path}')


class LoginView(GenericAPI):
    def get(self):
        return TemplateResponse(path='login.html')

    async def post(self, request: Request):
        # # COMMENTED FOR DEVELOPMENT
        # user: BaseUser = await config.USER_MODEL.find_one({config.USER_MODEL.USERNAME_FIELD: request.data['username']})
        # if user is None:
        #     raise AuthenticationAPIError
        #
        # if user.check_password(new_password=request.data['password']) is False:
        #     return AuthenticationAPIError

        return RedirectResponse(
            url=request.query_params.get('redirect_to', '..'),
            status_code=status.HTTP_302_FOUND,
            set_cookies=[
                Cookie(
                    key='access_token',
                    value=config.AUTHENTICATION.encode_jwt(str(self.id)),
                    max_age=config.JWT_CONFIG.life_time
                )
            ]
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
