# Configs

Panther collect all the configs from your `core/configs.py` or the module you passed directly to `Panther(configs=__name__)`


### [MONITORING](https://pantherpy.github.io/monitoring)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)
 
It should be `True` if you want to use `panther monitor` command
and see the monitoring logs

If `True`:

- Log every request in `logs/monitoring.log`

---
### [LOG_QUERIES](https://pantherpy.github.io/log_queries)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

If `True`:

- Calculate every query `perf time` & Log them in `logs/query.log`

---
### [MIDDLEWARES](https://pantherpy.github.io/middlewares)
> <b>Type:</b> `list` (<b>Default:</b> `[ ]`)

List of middlewares you want to use

---
### [AUTHENTICATION](https://pantherpy.github.io/authentications)
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

Every request goes through `authentication()` method of this `class` (if `auth = True`)

_Example:_ `AUTHENTICATION = 'panther.authentications.JWTAuthentication'`

---
### [WS_AUTHENTICATION](https://pantherpy.github.io/authentications)
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

WebSocket requests goes through `authentication()` method of this `class`, before the `connect()` (if `auth = True`)

_Example:_ `WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'`

---
### [URLs](https://pantherpy.github.io/urls)
> <b>Type:</b> `str` (<b>Required</b>)

It can be optional if you pass your `urls` directly to `Panther(urls=url_routing)`

It should be the address of your `urls` `dict`

_Example:_ `URLs = 'core.configs.urls.url_routing'`

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

---
### [BACKGROUND_TASKS](https://pantherpy.github.io/background_tasks/)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

If `True`:

- `initialize()` the `background_tasks`

---
### [STARTUP](https://pantherpy.github.io/startup)
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

It should be dotted address of your `startup` function,
this function can be `sync` or `async`

_Example:_ `STARTUP = 'core.configs.startup'`

---
### [SHUTDOWN](https://pantherpy.github.io/shutdown)
> <b>Type:</b> `str | None` (<b>Default:</b> `None`)

It should be dotted address of your `shutdown` function
this function can be `sync` or `async`

_Example:_ `SHUTDOWN = 'core.configs.shutdown'`

---
### [AUTO_REFORMAT](https://pantherpy.github.io/auto_reformat)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

It will reformat your code on every reload (on every change if you run the project with `--reload`) 

You may want to write your custom `ruff.toml` in root of your project.

Reference: [https://docs.astral.sh/ruff/formatter/](https://docs.astral.sh/ruff/formatter/)

_Example:_ `AUTO_REFORMAT = True`
