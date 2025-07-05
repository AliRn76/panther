from panther.authentications import CookieJWTAuthentication
from panther.exceptions import AuthenticationAPIError, RedirectAPIError
from panther.request import Request


class AdminCookieJWTAuthentication(CookieJWTAuthentication):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request=request)
        except AuthenticationAPIError:
            raise RedirectAPIError(url=f'login?redirect_to={request.path}')
