> <b>Variable:</b> `AUTHENTICATION`  
>  
> <b>Type:</b> `str`
>  
> <b>Default:</b> `None`
  
You can set your Authentication class in `core/configs.py`  then Panther will use this class for authentication in every `API` you set `auth=True` in `@API()`  _and put the `user` in `request.user` or `raise HTTP_401_UNAUTHORIZED` 


We already have one built-in authentication class which is used `jwt` for authentication and you can write your own authentication class too (we are going to disccuss about both of this scenarios)


### JWTAuthentication

#### Intro
This class will 
- get the `token` from `Authorization` header of request with keyword of `Bearer`
- then going to `decode` it 
- and find the match `user` with the `USER_MODEL` you have been already set

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
	'algorithm': 'HS256',  
	'life_time': timedelta(days=2),  
	'key': SECRET_KEY,  
}
```

> **key**             --> `Default` using your `SECRET_KEY`
> **algorithm**  --> `Default` using `HS256`
> **life_time**    --> `Default` using `timedelta(days=1)` 