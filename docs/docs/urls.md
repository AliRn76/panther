# URL Configuration in Panther

Panther requires you to define your application's URL routing. You can provide this configuration in two ways:

1. **Global Config:** Specify a dotted path to a dictionary of URLs in your configuration file.
2. **Direct Argument:** Pass the URL dictionary directly to the `Panther(...)` constructor (commonly used in single-file applications).

## How to Configure URLs

- The `URLs` config should be a dotted path (string) pointing to your root URL dictionary.
    - Example: `URLs = 'path.to.module.url_dict'`
- The target of `URLs` **must** be a Python `dict`.
- In the URL dictionary, each **key** is a URL path, and each **value** is either an endpoint (function/class) or another nested dictionary for sub-routing.

### Path Variables

You can define variables in your URL paths using angle brackets (`<variable_name>`):

- Example path: `user/<user_id>/blog/<title>/`
- The corresponding endpoint must accept parameters with the same names.
- Panther will automatically cast arguments to the expected types and raise an error if the types do not match.

=== "Function-based"
    ```python title="app/apis.py"
    @API()
    async def profile_api(user_id: int, title: str, is_alive: bool):
        ...
    ```

=== "Class-based"
    ```python title="app/apis.py"
    class MyAPI(GenericAPI):
        async def get(self, user_id: int, title: str, is_alive: bool):
            ...
    ```

---

## Example: Global Config Structure
Specify a dotted path to a dictionary of URLs in your configuration file.

```
.
├── app
│     ├── apis.py
│     └── urls.py
└── core
      ├── configs.py
      └── urls.py
```

```python title="core/configs.py"
URLs = 'core.urls.url_routing'
```

```python title="core/urls.py" linenums="1"
from app.urls import app_urls

url_routing = {
    'user/': app_urls,
}
```

```python title="app/urls.py" linenums="1"
from app.apis import *

app_urls = {
    'login/': login_api,
    'logout/': logout_api,
    '<user_id>/blog/<title>/<is_alive>/': profile_api,
}
```

```python title="app/apis.py" linenums="1"
from panther import API

@API()
async def profile_api(user_id: int, title: str, is_alive: bool):
    ...
```

---

## Example: Single-File Structure

You can pass the URL dictionary directly to Panther:

```python title="main.py"
# Other codes ...

urls = {
    '/': first_api,
}

app = Panther(__name__, configs=__name__, urls=urls)
```
