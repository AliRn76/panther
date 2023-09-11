> <b>Variable:</b> `URLs` 
> 
> <b>Type:</b> `str` 
> 
> <b>Required:</b> `True`

- `URLs` should point to your root `urls` with dotted address (`path.module.url_dict`),
and it should be `dict`.
- `key` of url_routing dict is `path` & value is `endpoint` or another `dict`

- #### Path Variables are handled like below:

    - <`variable_name`>
    - Example: `user/<user_id>/blog/<title>/`
    - The `endpoint` should have parameters with those names too
    - Example: `async def profile_api(user_id: int, title: str):`

## Example

- core/configs.py
    ```python
    `URLs = 'core.urls.url_routing`
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