

## Panther 
<b>Is A Fast &  Friendly Web Framework For Building Async APIs With Python 3.11+</b> 

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="logo" style="width: 450px">
</p>

<p>
  <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" alt="logo" style="width: 50px;">
   <b>Supported by </b><a href="https://jb.gg/OpenSourceSupport">JetBrain</a>
</p>

**_Full Documentation:_** [https://pantherpy.github.io](https://pantherpy.github.io)

**_GitHub:_** [https://github.com/AliRn76/panther](https://github.com/AliRn76/panther)

**_PyPI:_** [https://pypi.org/project/panther/](https://pypi.org/project/panther/)

---

### Why Use Panther ?
- Document-oriented Databases ODM ([PantherDB](https://pypi.org/project/pantherdb/), MongoDB)
- Visual API Monitoring (In Terminal)
- Cache APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares
- Handle Custom Throttling 
---

### Installation
- <details open>
    <summary>Create a Virtual Environment</summary>
    <pre>$ python3 -m venv .venv</pre>
  
  </details>
  
- <details open>
    <summary>Active The Environment</summary>
    * Linux & Mac
      <pre>$ source .venv/bin/activate</pre>
    * Windows
      <pre>$ .\\.venv\Scripts\activate</pre>
  
  </details>
 
- <details open>
    <summary>Install Panther</summary>
    * Normal
      <pre>$ pip install panther</pre>
    * Include MongoDB Requirements
      <pre>$ pip install panther[full]</pre>
  </details>
  
---

### Usage

- #### Create Project

    ```console
    $ panther create <project_name> <directory>
    ```

- #### Run Project

    Panther uses [Uvicorn](https://github.com/encode/uvicorn) as ASGI (Asynchronous Server Gateway Interface)
    
    ```console
    $ panther run 
    ```

- #### Monitoring Requests

    ```console
    $ panther monitor 
    ```

- #### Python Shell

    Panther Uses [bpython](https://bpython-interpreter.org) for shell
    
    ```console
    $ panther shell 
    ```
  
### Example

- #### You can create project with
 
    ```console 
    $ panther create myproject
    ``` 
  
- #### or create it yourself:

    **core/configs.py**:
    
    ```python
    URLs = 'core/urls.py'
    ```
    
    **core/urls.py**:
    
    ```python
    from app.urls import urls as app_urls
    
    urls = {
        '/': app_urls,
    }
    ```
    
    **app/urls.py**:
    
    ```python
    from app.apis import hello_world, info
    
    urls = {
        '': hello_world,
        'info/': info,
    }
    ```
    
    **app/apis.py**:
    
    ```python
    from datetime import datetime, timedelta

    from panther.app import API
    from panther.configs import config
    from panther import version, status
    from panther.request import Request
    from panther.response import Response
    from panther.throttling import Throttling
    
    
    InfoThrottling = Throttling(rate=5, duration=timedelta(minutes=1))
  
    @API()
    async def hello_world():
        return {'detail': 'Hello World'}
    
    
    @API(cache=True, throttling=InfoThrottling)
    async def info(request: Request):
        data = {
            'version': version(),
            'datetime_now': datetime.now().isoformat(),
            'user_agent': request.headers.user_agent,
            'db_engine': config['db_engine'],
        }
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
    ```

- <b> Then run (`$ panther run`) the project, now you can see these two urls:</b>

  * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

  * [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)



> Writing Your First CRUD: [First CRUD](https://pantherpy.github.io/first_crud)
