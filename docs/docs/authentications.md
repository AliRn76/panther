> <b>Variable:</b> `AUTHENTICATION` & `WS_AUTHENTICATION`  
>  
> <b>Type:</b> `str`
>  
> <b>Default:</b> `None`

You can set Authentication class in your `configs` 

Panther use it, to authenticate every API/ WS if `auth=True` and give you the user or `raise HTTP_401_UNAUTHORIZED`

The `user` will be in `request.user` in APIs and in `self.user` in WSs 

--- 

We implemented 2 built-in authentication classes which use `JWT` for authentication.

But, You can use your own custom authentication class too.

--- 

### JWTAuthentication

This class will 

- Get the `token` from `Authorization` header of request.
- Check the `Bearer`
- `decode` the `token` 
- Find the matched `user`

> `JWTAuthentication` is going to use `panther.db.models.BaseUser` if you didn't set the `USER_MODEL` in your `configs`

You can customize these 4 variables for `JWTAuthentication` in your `configs` as `JWTConfig` like below (`JWTConfig` is optional):

```python
...
from datetime import timedelta
from panther.utils import load_env  
from pathlib import Path
  
BASE_DIR = Path(__name__).resolve().parent  
env = load_env(BASE_DIR / '.env')

SECRET_KEY = env['SECRET_KEY']

JWTConfig = {  
	'key': SECRET_KEY,  
	'algorithm': 'HS256',  
	'life_time': timedelta(days=2),  
	'refresh_life_time': timedelta(days=10),  
}
```

> **key** &emsp;&emsp;&emsp;&emsp;--> default is `SECRET_KEY`
> 
> **algorithm** &emsp; --> default is `HS256`
> 
> **life_time**&emsp;&emsp;--> default is `timedelta(days=1)` 
>
> **refresh_life_time**&emsp;&emsp;--> default is `multiply 2 of life_time` 

### QueryParamJWTAuthentication

- This class is same as `JWTAuthentication` and the only difference is that, this class is looking for token in `query params` not in the `headers`

- You should pass the token like this:
  > https://example.com/path?authorization=Bearer%20access_token


#### Websocket Authentication
The `QueryParamJWTAuthentication` is very useful when you are trying to authenticate the user in websocket, you just have to add this into your `configs`:
```python
WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```


### Custom Authentication
- Create a class and inherits it from `panther.authentications.BaseAuthentication`


- Implement `async authentication(cls, request: Request | Websocket)` method
    - Process the `request.headers.authorization` or ...
    - Return Instance of `USER_MODEL`
    - Or raise `panther.exceptions.AuthenticationAPIError` 
  

- Add it into your `configs`
  ```python
  AUTHENTICATION = 'project_name.core.authentications.CustomAuthentication'
  ```

> You can see the source code of JWTAuthentication [[here]](https://github.com/AliRn76/panther/blob/da2654ccdd83ebcacda91a1aaf51d5aeb539eff5/panther/authentications.py) 