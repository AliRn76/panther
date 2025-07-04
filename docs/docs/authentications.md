# Authentication in Panther

Authentication in Panther ensures that only authorized users can access your APIs and WebSocket connections. You can configure which authentication class to use in your `configs`.

---

## How Authentication Works

- The `auth` parameter for an API or WebSocket should be an async function or a class with an async `__call__` method. Panther will use this callable to verify the user.
- If you do not set `auth`, Panther will use the default `AUTHENTICATION` from your config **only if the request contains an authorization header**. If there is no authorization header, authentication is bypassed and `request.user` will be `None`.
- If authentication fails, Panther raises `HTTP_401_UNAUTHORIZED`.
- The authenticated user is available as:
  - `request.user` in API views
  - `self.user` in WebSocket connections

> **Note:** When authentication is bypassed (no authorization header), `request.user` will be `None` and you must rely on permissions to check the user and their authorization.

---

## Built-in Authentication Classes

Panther provides three built-in authentication classes, all based on JWT (JSON Web Token):

### 1. JWT Authentication

- Retrieves the JWT token from the `Authorization` header in the request.
- Expects the header format: `Authorization: Bearer <token>`
- Decodes the token, validates it, and fetches the corresponding user.
- By default, uses `panther.db.models.BaseUser` as the user model unless you set `USER_MODEL` in your configs.
- Handles token revocation if Redis is connected (for logout and refresh scenarios).

#### Example usage
```python
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
```

#### JWT Configuration
You can customize JWT behavior by setting `JWT_CONFIG` in your configs. Example:

```python title="core/configs.py" linenums="1"
from datetime import timedelta
from panther.utils import load_env  
from pathlib import Path

BASE_DIR = Path(__name__).resolve().parent  
env = load_env(BASE_DIR / '.env')

SECRET_KEY = env['SECRET_KEY']

JWT_CONFIG = {
    'key': SECRET_KEY,              # Secret key for signing tokens (default: `SECRET_KEY`)
    'algorithm': 'HS256',           # Algorithm used for JWT (default: `'HS256'`)
    'life_time': timedelta(days=2), # Access token lifetime (default: `timedelta(days=1)`)
    'refresh_life_time': timedelta(days=10), # Refresh token lifetime (default: `2 * life_time`)
}
```

---

### 2. QueryParam JWT Authentication

- Works like `JWTAuthentication`, but expects the token in the query parameters instead of headers.
- Useful for WebSocket authentication or scenarios where headers are not available.
- Pass the token as a query parameter:
  - Example: `https://example.com?authorization=<jwt_token>`

#### Example usage
```python
AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```

---

### 3. Cookie JWT Authentication

- Works like `JWTAuthentication`, but expects the token in cookies.
- Looks for `access_token` in cookies for authentication.
- Optionally, can use `refresh_token` in cookies for token refresh.
- Pass the token in cookies:
  - Example: `Cookies: access_token=<jwt_token>`

#### Example usage
```python
AUTHENTICATION = 'panther.authentications.CookieJWTAuthentication'
```

---

## WebSocket Authentication

For WebSocket connections, it is recommended to use `QueryParamJWTAuthentication` since headers are not always available. To enable this, set the following in your configs:

```python
WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```

---

## Custom Authentication

You can implement your own authentication logic by either:
- Inheriting from `panther.authentications.BaseAuthentication` and implementing an async `__call__` method (recommended for consistency), or
- Providing any async function or class with an async `__call__` method.

### Steps to create a custom authentication class:
1. **Inherit from `BaseAuthentication` and implement async `__call__`**
   ```python
   from panther.request import Request
   from panther.exceptions import AuthenticationAPIError
   from panther.authentications import BaseAuthentication

   class CustomAuthentication(BaseAuthentication):
       async def __call__(self, request: Request):
           # Your authentication logic here
           # Return an instance of USER_MODEL (default: BaseUser)
           # Or raise AuthenticationAPIError on failure
           ...
   ```
   Or as a function or plain class:
   ```python
   async def custom_authentication(request: Request):
       # Your authentication logic here
       # Return an instance of USER_MODEL (default: BaseUser)
       # Or raise AuthenticationAPIError on failure
       ...
   ```
2. **Configure your custom authentication class or function in your configs (if you want it as default):**
   ```python
   AUTHENTICATION = 'project_name.core.authentications.CustomAuthentication'
   ```
3. **Or set it per API using the `auth` parameter:**
   ```python
   @API(auth=CustomAuthentication)
   async def my_api(request: Request):
       ...
   ```

---

## Error Handling
- If authentication fails, raise `panther.exceptions.AuthenticationAPIError` with an appropriate message.
- Panther will automatically handle and return a 401 Unauthorized response.

---

## Summary
- Choose and configure the appropriate authentication class or function for your use case.
- Use JWT configuration options to control token behavior.
- For WebSocket, prefer query parameter-based authentication.
- Implement custom authentication as an async function or a class with an async `__call__` method.
- If authentication is bypassed, `request.user` will be `None` and you must use permissions to check the user and their authorization.
