If you want to work with `Panther` in a `single-file` structure, follow the steps below.

## Steps

1. Write your `APIs` as you like

    ```python
    from panther.app import API
    
    @API()
    async def hello_world_api():
        return {'detail': 'Hello World'}
    ```

2. Add your `APIs` to a `dict` (example: `url_routing`)

    ```python
    from panther.app import API
    
    @API()
    async def hello_world_api():
        return {'detail': 'Hello World'}
    
    url_routing = {
        '/': hello_world_api,
    }
    ```
3. Create an `app` and pass your current `module name` and `urls` to it.

    ```python
    from panther import Panther
    from panther.app import API
    
    @API()
    async def hello_world_api():
        return {'detail': 'Hello World'}
    
    url_routing = {
        '/': hello_world_api,
    }
    
    app = Panther(__name__, configs=__name__, urls=url_routing)
    ```
4. Run the project

    - If name of your file is `main.py` --> 
    ```panther run```
   - else use `uvicorn` -->
   ```uvicorn file_name:app```

### Notes
- `URLs` is a required config unless you pass the `urls` directly to the `Panther`  
- When you pass the `configs` to the `Panther(configs=...)`, Panther is going to load the configs from this file, 
else it is going to load `core/configs.py` file

   ```python
   from panther import Panther
   from panther.app import API
   
   @API()
   async def hello_world_api():
        return {'detail': 'Hello World'}
   
   url_routing = {
        '/': hello_world_api,
   }
   
   app = Panther(__name__, configs=__name__, urls=url_routing)
   ```