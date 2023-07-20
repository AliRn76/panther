> <b>Variable:</b> `URLs` 
> 
> <b>Type:</b> `str` 
> 
> <b>Required:</b> `True`

- `URLs` should point to the root of your `urls` file,
and in that file you should have a `dict` name `urls`
- `key` of urls dict is `path` & value is `endpoint` or another `dict`

- #### Path Variables are handled like below:

    - <`variable_name`>
    - Example: `user/<user_id>/blog/<title>/`
    - The `endpoint` should have parameters with those names too
    - Example: `async def profile_api(user_id: int, title: str):`

## Example

- core/configs.py
    ```python
    `URLs = 'configs/urls.py'`
    ```
- core/urls.py
    ```python
    from app.urls import app_urls

    urls = {
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