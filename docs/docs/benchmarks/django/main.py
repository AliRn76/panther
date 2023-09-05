import json

from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import path


# Main API
async def main_api(request, user, record):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if request.method != 'PUT':
        return HttpResponseNotAllowed(['PUT'])

    if not request.headers.get('authorization'):
        return JsonResponse(data={'detail': 'Authorization Error'}, status=401)

    data = {
        'params': {'user': user, 'record': record},
        'query': dict(request.GET),
        'data': json.loads(request.body.decode() or '{}'),
    }
    return JsonResponse(data=data, status=200)


# Fake API
async def fake_api(*args, **kwargs):
    return JsonResponse(data={'detail': 'Ok'}, status=202)


# Routing
pre_fake_urlpatterns = [path('users/<int:user>/', fake_api) for n in range(50)]
main_urlpatterns = [path('users/<int:user>/records/<int:record>',  main_api)]
post_fake_urlpatterns = [path(f'fake-route-{n}/<part>', fake_api) for n in range(50)]

urlpatterns = pre_fake_urlpatterns + main_urlpatterns + post_fake_urlpatterns


# Project Config
settings.configure(SECRET_KEY='SecretKey', DEBUG=False, ROOT_URLCONF=__name__)
app = get_asgi_application()
