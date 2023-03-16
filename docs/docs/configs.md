# Configs

Panther  stores all the configs in the `core/configs.py`


### MONITORING
> <b>Type:</b> `bool` (<b>Default:</b> `False`)
 
It should be `True` if you want to use `panther monitor` command
and see the monitoring logs

If `True` it will:

- Log every request


### LOG_QUERIES
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

If `True` it will:

- Calculate every query perf time

---
### MIDDLEWARES
> <b>Type:</b> `list` (<b>Default:</b> `[ ]`)

List of middlewares you want to use

[read more ...](https://pantherpy.github.io/middlewares)

---
### AUTHENTICATION
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

Every request go through `authentication()` method of this `class`

_Example:_ `AUTHENTICATION = 'panther.authentications.JWTAuthentication'`

[read more ...](https://pantherpy.github.io/authentication)

---
### URLs
> <b>Type:</b> `str` (<b>Required</b>)

It should be the address of your `urls` `dict`

_Example:_ `URLS = 'configs/urls.py'`

[read more ...](https://pantherpy.github.io/urls)

---
### DEFAULT_CACHE_EXP
> <b>Type:</b> `timedelta| None` (<b>Default:</b> `None`)

It uses while you are using `cache=True` in `@API` decorator

[read more ...](https://pantherpy.github.io/cache)
