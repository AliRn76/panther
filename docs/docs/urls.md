> <b>Variable:</b> `URLs` 
> 
> <b>Type:</b> `str` 
> 
> <b>Required:</b> `True`

- `URLs` should point to your root `urls` with dotted address (`path.module.url_dict`)
- The target of `URLs` should be `dict`.
- The `key` in `url_routing` is the `path` & value is the `endpoint` or another `dict`

- #### Path Variables are handled like below:

    - <`variable_name`>
    - Example: `user/<user_id>/blog/<title>/`
    - The `endpoint` should have parameters with those names too
    - Example Function-Base: `async def profile_api(user_id: int, title: str):`
    - Example Class-Base: `async def get(self, user_id: int, title: str):`

## Example

- `configs`
    ```python
    URLs = 'core.urls.url_routing
    ```
- core/urls.py
    ```python
    from app.urls import app_urls

    url_routing = {
        'user/': app_urls,
    }
    ```
- app/urls.py
    ```python
    from app.apis import *
    
    urls = {
        'login/': login_api,
        'logout/': logout_api,
        'profile/<user_id>/': profile_api,
    }
    ```

- app/apis.py
    ```python
    ...
    
    @API()
    async def profile_api(user_id: int):
        return User.find_one(id=user_id)
    ```