# Configs

Panther  stores all the configs in the `core/configs.py`


### [MONITORING](https://pantherpy.github.io/monitoring)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)
 
It should be `True` if you want to use `panther monitor` command
and see the monitoring logs

If `True` it will:

- Log every request in `logs/monitoring.log`

---
### [LOG_QUERIES](https://pantherpy.github.io/log_queries)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

If `True` it will:

- Calculate every query perf time & Log them in `logs/query.log`

---
### [MIDDLEWARES](https://pantherpy.github.io/middlewares)
> <b>Type:</b> `list` (<b>Default:</b> `[ ]`)

List of middlewares you want to use

---
### [AUTHENTICATION](https://pantherpy.github.io/authentications)
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

Every request goes through `authentication()` method of this `class`

_Example:_ `AUTHENTICATION = 'panther.authentications.JWTAuthentication'`

---
### [URLs](https://pantherpy.github.io/urls)
> <b>Type:</b> `str` (<b>Required</b>)

It should be the address of your `urls` `dict`

_Example:_ `URLS = 'configs.urls.url_routing'`

---
### [DEFAULT_CACHE_EXP](https://pantherpy.github.io/caching)
> <b>Type:</b> `timedelta| None` (<b>Default:</b> `None`)

We use it as default `cache_exp_time` you can overwrite it in your `@API` too

It is used when you set `cache=True` in `@API` decorator

_Example:_ `DEFAULT_CACHE_EXP = timedelta(seconds=10)`

---
### [THROTTLING](https://pantherpy.github.io/throttling)
> <b>Type:</b> `Throttling | None` (<b>Default:</b> `None`)

We use it as default `throttling` you can overwrite it in your `@API` too

_Example:_ `THROTTLING = Throttling(rate=10, duration=timedelta(seconds=10))`

---
### [USER_MODEL](https://pantherpy.github.io/user_model)
> <b>Type:</b> `str | None` (<b>Default:</b> `'panther.db.models.BaseUser'`)

It is used for authentication

_Example:_ `USER_MODEL = 'panther.db.models.User'`

---
### [JWTConfig](https://pantherpy.github.io/jwt)
> <b>Type:</b> `dict | None` (<b>Default:</b> `JWTConfig = {'key': SECRET_KEY}`)

We use it when you set `panther.authentications.JWTAuthentication` as `AUTHENTICATION`
