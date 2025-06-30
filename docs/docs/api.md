# Panther API Guide

This guide assumes you have successfully set up your project and created your first CRUD following the [First CRUD](first_crud.md) guide.

In this guide, we discuss the features and structure of Panther's API system, including authentication, permissions, caching, throttling, middlewares, and more.

---

## API Request Flow

The typical flow of an API request in Panther is as follows:

```
Middlewares
├── Method
├── Authentication
├── Permissions
├── Throttling
├── Validate Input
├── Get Response From Cache
├── Call Endpoint
├── Set Response To Cache
Middlewares
```

---

## Input Model

You can validate incoming data using the `input_model` parameter. Pass a serializer to it, and Panther will send `request.data` to this serializer, placing the validated data in `request.validated_data`. As a result, `request.validated_data` will be an instance of your serializer.

> Note: `request.data` is validated only for 'POST', 'PUT', and 'PATCH' methods.

??? question "How do serializers work in Panther?"
    Refer to [Serializer](serializer.md) to learn more about serializers.

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response
    
    
    @API(auth=True)
    async def user_api(request: Request):
        user = request.user
        return Response(data=user, status_code=status.HTTP_200_OK)
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    
    class UserAPI(GenericAPI):
        auth = True
    
        async def get(self, request: Request):
            user = request.user
            return Response(data=user, status_code=status.HTTP_200_OK)
    ```

---

## Output Model

Use the `output_model` parameter to automatically serialize your API response data using a specified serializer. This ensures that the response structure is consistent and validated.

**Example Serializer:**

```python title="app/serializers.py" linenums="1"
from panther.serializer import ModelSerializer

class UserSerializer(ModelSerializer):
    ...
```

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import API
    from app.serializers import UserSerializer
    
    @API(output_model=UserSerializer)
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import GenericAPI
    from app.serializers import UserSerializer
    
    class UserAPI(GenericAPI):
        output_model = UserSerializer
        ...
    ```

> **Tip:** Use `output_model` to ensure your API always returns data in the expected format. For OpenAPI documentation, see the `output_schema` section.

---

## Authentication

To ensure that each request contains a valid authentication header, set `auth=True`. Panther will look for the `AUTHENTICATION` class from your config and use its `authentication()` method for this purpose.

??? question "How do authentications work in Panther?"
    Refer to [Authentications](authentications.md) to learn more about authentications.

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response
    
    @API(auth=True)
    async def user_api(request: Request):
        user = request.user
        return Response(data=user, status_code=status.HTTP_200_OK)
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    class UserAPI(GenericAPI):
        auth = True
    
        async def get(self, request: Request):
            user = request.user
            return Response(data=user, status_code=status.HTTP_200_OK)
    ```

---

## Method

You can specify which HTTP methods are allowed for an endpoint by setting `methods` in function-based APIs. Only the following methods are supported: `['GET', 'POST', 'PUT', 'PATCH', 'DELETE']`.

> If a method is not allowed, a 405 status code will be returned.

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import API
    from panther.request import Request
    
    @API(methods=['GET', 'POST'])
    async def user_api(request: Request):
        match request.method:
            case 'GET':
                ...
            case 'POST':
                ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import GenericAPI
    
    class UserAPI(GenericAPI):  # (1)!
        async def get(self):
            ...
    
        async def post(self):
            ...
    ```

    1. Now this class only accepts `GET` and `POST` requests.

---

## Permissions

You can implement your authorization logic using permission classes. Any class that inherits from `panther.permissions.BasePermission` or implements an `authorization()` method can be used as a permission class.

Pass a list of permission classes to your API, and Panther will call each class's `authorization()` method. If any return `False`, a `panther.exceptions.AuthorizationAPIError` will be raised.

> The `authorization()` method should be an `async classmethod`.

**Example Permission Class:**

```python title="app/permissions.py" linenums="1"
from panther.permissions import BasePermission
from panther.request import Request

class CustomPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return True
```

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import API
    from app.permissions import CustomPermission
    
    @API(permissions=[CustomPermission])
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import GenericAPI
    from app.permissions import CustomPermission
    
    class UserAPI(GenericAPI):
        permissions = [CustomPermission]
        ...
    ```

---

## Cache

Responses can be cached for a specific amount of time per request or IP. Caching is only applied to `GET` requests. The response's headers, data, and status code will be cached.

The cache is stored in Redis (if connected) or in memory. The cache key is based on the user ID or IP, request path, query parameters, and validated data:

```
'user_id or ip - request.path - hash of query param - request.validated_data'
```

The value of `cache` should be an instance of `datetime.timedelta()`.

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from datetime import timedelta
    from panther.app import API
    
    @API(cache=timedelta(minutes=10))
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from datetime import timedelta
    from panther.app import GenericAPI
    
    class UserAPI(GenericAPI):
        cache = timedelta(minutes=10)
        ...
    ```

---

## Throttling

You can throttle requests using the `Throttle` class, either globally via the `THROTTLING` config or per API. The `Throttle` class has two fields: `rate` and `duration`.

If a user exceeds the allowed number of requests (`rate`) within the specified `duration`, they will receive a `429 Too Many Requests` response and be banned for the duration.

> When you set `throttling` on your API, it takes precedence over the default `THROTTLING`, and the default `THROTTLING` will not be executed.

### Setting Default Throttling

```python
from datetime import timedelta
from panther.throttling import Throttle

# Users can only make 5 requests every minute
THROTTLING = Throttle(rate=5, duration=timedelta(minutes=1))
```

### Throttling Per API

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from datetime import timedelta
    from panther.app import API
    from panther.throttling import Throttle
    
    @API(throttling=Throttle(rate=5, duration=timedelta(minutes=1)))
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from datetime import timedelta
    from panther.app import GenericAPI
    from panther.throttling import Throttle
    
    class UserAPI(GenericAPI):
        throttling = Throttle(rate=5, duration=timedelta(minutes=1))
        ...
    ```

### Customization

Throttling works with `request.user.id` or `request.client.ip`. You can customize its behavior by overriding `build_cache_key()`:

```python title="app/throttlings.py" linenums="1"
from panther.request import Request
from panther.throttling import Throttle

class CustomThrottle(Throttle):
    def build_cache_key(self, request: Request) -> str:
        ...
```

---

## Middlewares

You can pass custom middlewares to specific APIs.

**Example Middleware:**

```python title="app/middlewares.py" linenums="1"
from panther.middlewares.base import HTTPMiddleware
from panther.request import Request
from panther.response import Response

class CustomMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request) -> Response:
        print('Hi')
        response = await self.dispatch(request=request)
        print('Bye')
        return response
```

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import API
    from app.middlewares import CustomMiddleware 
    
    @API(middlewares=[CustomMiddleware])
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import GenericAPI
    from app.middlewares import CustomMiddleware 
    
    class UserAPI(GenericAPI):
        middlewares = [CustomMiddleware]
        ...
    ```

??? question "How do middlewares work in Panther?"
    Refer to [Middlewares](middlewares.md) to learn more about middlewares.

---

## Output Schema

The `output_schema` attribute is used when generating OpenAPI (Swagger) documentation. 
It should be an instance of `panther.openapi.OutputSchema`, which specifies the desired response data structure and status code.

**Example Serializer:**

```python title="app/serializers.py" linenums="1"
from panther.serializer import ModelSerializer

class UserSerializer(ModelSerializer):
    ...
```

=== "Function-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther import status
    from panther.app import API
    from panther.openapi import OutputSchema
    from app.serializers import UserSerializer
    
    @API(output_schema=OutputSchema(status_code=status.HTTP_201_CREATED, model=UserSerializer))
    async def user_api():
        ...
    ```

=== "Class-Base API"

    ```python title="app/apis.py" linenums="1"
    from panther.app import GenericAPI
    from panther.openapi import OutputSchema
    from app.serializers import UserSerializer
    
    class UserAPI(GenericAPI):
        output_schema = OutputSchema(status_code=status.HTTP_201_CREATED, model=UserSerializer)
        ...
    ```

??? question "How does OpenAPI work in Panther?"
    Refer to [OpenAPI](open_api.md) to learn more about OpenAPI.

