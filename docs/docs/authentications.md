> <b>Variable:</b> `AUTHENTICATION`  
>  
> <b>Type:</b> `str`
>  
> <b>Default:</b> `None`
  
You can set your Authentication class in `configs`, now, if you set `auth=True` in `@API()`, Panther will use this class for authentication of every `API`, and put the `user` in `request.user` or `raise HTTP_401_UNAUTHORIZED` 

We implemented a built-in authentication class which used `JWT` for authentication.
But, You can use your own custom authentication class too.


### JWTAuthentication

This class will 

- Get the `token` from `Authorization` header of request.
- Check the `Bearer`
- `decode` the `token` 
- Find the matched `user` (It uses the `USER_MODEL`)

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


### Custom Authentication
- Create a class and inherits it from `panther.authentications.BaseAuthentication`


- Implement `async authentication(cls, request: Request | Websocket)` method
    - Process the `request.headers.authorization` or ...
    - Return Instance of `USER_MODEL`
    - Or raise `panther.exceptions.AuthenticationAPIError` 
  

- Address it in `configs`
  - `AUTHENTICATION = 'project_name.core.authentications.CustomAuthentication'`

> You can see the source code of JWTAuthentication [[here]](https://github.com/AliRn76/panther/blob/da2654ccdd83ebcacda91a1aaf51d5aeb539eff5/panther/authentications.py#L38) 