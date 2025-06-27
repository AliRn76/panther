# Configs

Panther collect all the configs from your `core/configs.py` or the module you passed directly to `Panther(configs=__name__)`


### [LOG_QUERIES](https://pantherpy.github.io/log_queries)
> <b>Type:</b> `bool` (<b>Default:</b> `False`)

If `True`:

- Calculate every query `perf time` & Log them in `logs/query.log`

---

---
### [TEMPLATES_DIR](https://pantherpy.github.io/templates_dir)
> <b>Type:</b> `str | list[str]` (<b>Default:</b> `'tempaltes'`)

We use it when want to have different template directories

_Example:_ `TEMPLATES_DIR = ['templates', 'app/templates']

---
### [USER_MODEL](https://pantherpy.github.io/user_model)
> <b>Type:</b> `str | None` (<b>Default:</b> `'panther.db.models.BaseUser'`)

It is used for authentication

_Example:_ `USER_MODEL = 'panther.db.models.User'`
