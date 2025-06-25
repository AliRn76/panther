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
- **Function-based example:**
  ```python
  @API()
  async def profile_api(user_id: int, title: str):
      ...
  ```
- **Class-based example:**
  ```python
  class MyAPI(GenericAPI):
      async def get(self, user_id: int, title: str):
          ...
  ```

---

## Example: Global Config Structure

**core/configs.py**
```python
URLs = 'core.urls.url_routing'
```

**core/urls.py**
```python
from app.urls import app_urls

url_routing = {
    'user/': app_urls,
}
```

**app/urls.py**
```python
from app.apis import *

app_urls = {
    'login/': login_api,
    'logout/': logout_api,
    '<user_id>/blog/<title>/': profile_api,
}
```

**app/apis.py**
```python
from panther import API

@API()
async def profile_api(user_id: int, title: str):
    ...
```

---

## Example: Single-File Structure

You can pass the URL dictionary directly to Panther:

```python
urls = {
    '/': first_api,
}

app = Panther(__name__, configs=__name__, urls=urls)
```
