> <b>Variable:</b> `AUTHENTICATION`  
>  
> <b>Type:</b> `str`
>  
> <b>Default:</b> `None`
  
You can set your Authentication class in `core/configs.py`, then Panther will use this class for authentication in every `API`, if you set `auth=True` in `@API()`, and put the `user` in `request.user` or `raise HTTP_401_UNAUTHORIZED` 


We already have one built-in authentication class which is used `JWT` for authentication.

You can write your own authentication class too (we are going to discuss it)


### JWTAuthentication

This class will 

- Get the `token` from `Authorization` header of request with keyword of `Bearer`
- `decode` it 
- Find the match `user` in `USER_MODEL` you have already set

> `JWTAuthentication` is going to use `panther.db.models.BaseUser` if you didn't set the `USER_MODEL` in your `core/configs.py`

You can customize these 3 variables for `JWTAuthentication` in your `core/configs.py` as `JWTConfig` like below (`JWTConfig` is optional):

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
}
```

> **key** &emsp;&emsp;&emsp;&emsp;--> default is `SECRET_KEY`
> 
> **algorithm** &emsp; --> default is `HS256`
> 
> **life_time**&emsp;&emsp;--> default is `timedelta(days=1)` 


### Custom Authentication
- Create a class and inherits it from `panther.authentications.BaseAuthentication`


- Implement `authentication(cls, request: Request)` method
    - Process the `request.headers.authorization` or ...
    - Return Instance of `USER_MODEL`
    - Or raise `panther.exceptions.AuthenticationException` 
  

- Address it in `core/configs.py`
  - `AUTHENTICATION = 'project_name.core.authentications.CustomAuthentication'`

> You can look at the source code of JWTAuthentication for 