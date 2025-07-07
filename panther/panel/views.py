import logging

from panther import status
from panther.app import GenericAPI
from panther.configs import config
from panther.db.models import BaseUser
from panther.panel.authentications import AdminCookieJWTAuthentication
from panther.panel.middlewares import RedirectToSlashMiddleware
from panther.panel.permissions import IsAuthenticated
from panther.panel.utils import clean_model_schema, get_models, serialize_models
from panther.request import Request
from panther.response import Cookie, RedirectResponse, Response, TemplateResponse

logger = logging.getLogger('panther')


class LoginView(GenericAPI):
    middlewares = [RedirectToSlashMiddleware]

    def get(self, request: Request):
        return TemplateResponse(name='login.html')

    async def post(self, request: Request):
        from panther.authentications import JWTAuthentication

        user: BaseUser = await config.USER_MODEL.find_one({config.USER_MODEL.USERNAME_FIELD: request.data['username']})
        if user is None:
            logger.debug('User not found.')
            return TemplateResponse(
                name='login.html',
                status_code=status.HTTP_400_BAD_REQUEST,
                context={'error': 'Authentication Error'},
            )
        if user.check_password(password=request.data['password']) is False:
            logger.debug('Password is incorrect.')
            return TemplateResponse(
                name='login.html',
                status_code=status.HTTP_400_BAD_REQUEST,
                context={'error': 'Authentication Error'},
            )
        tokens = await JWTAuthentication.login(user=user)
        return RedirectResponse(
            url=request.query_params.get('redirect_to', '..'),
            status_code=status.HTTP_302_FOUND,
            set_cookies=[
                Cookie(key='access_token', value=tokens['access_token'], max_age=config.JWT_CONFIG.life_time),
                Cookie(key='refresh_token', value=tokens['refresh_token'], max_age=config.JWT_CONFIG.refresh_life_time),
            ],
        )


class HomeView(GenericAPI):
    auth = AdminCookieJWTAuthentication
    permissions = IsAuthenticated

    def get(self):
        return TemplateResponse(name='home.html', context={'tables': get_models()})


class TableView(GenericAPI):
    auth = AdminCookieJWTAuthentication
    permissions = IsAuthenticated
    middlewares = [RedirectToSlashMiddleware]

    async def get(self, request: Request, index: int):
        model = config.MODELS[index]
        if data := await model.find():
            data = data
        else:
            data = []

        return TemplateResponse(
            name='table.html',
            context={
                'fields': clean_model_schema(model.model_json_schema()),
                'tables': get_models(),
                'records': serialize_models(data),
            },
        )


class CreateView(GenericAPI):
    auth = AdminCookieJWTAuthentication
    permissions = IsAuthenticated
    middlewares = [RedirectToSlashMiddleware]

    async def get(self, request: Request, index: int):
        model = config.MODELS[index]
        return TemplateResponse(
            name='create.html',
            context={
                'fields': clean_model_schema(model.model_json_schema()),
                'tables': get_models(),
            },
        )

    async def post(self, request: Request, index: int):
        model = config.MODELS[index]
        request.validate_data(model=model)
        instance = await model.insert_one(request.validated_data.model_dump())
        if issubclass(model, BaseUser):
            await instance.set_password(password=instance.password)
        return instance


class DetailView(GenericAPI):
    auth = AdminCookieJWTAuthentication
    permissions = IsAuthenticated
    middlewares = [RedirectToSlashMiddleware]

    async def get(self, index: int, document_id: str):
        model = config.MODELS[index]
        obj = await model.find_one_or_raise(id=document_id)
        return TemplateResponse(
            name='detail.html',
            context={'fields': clean_model_schema(model.model_json_schema()), 'data': obj.model_dump()},
        )

    async def put(self, request: Request, index: int, document_id: str):
        model = config.MODELS[index]
        request.validate_data(model=model)
        await model.update_one({'id': document_id}, request.validated_data.model_dump())
        return await model.find_one(id=document_id)

    async def delete(self, index: int, document_id: str):
        model = config.MODELS[index]
        await model.delete_one(id=document_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
