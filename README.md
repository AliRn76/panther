
[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![license](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)


## Panther 
<b>Is A Fast &  Friendly Web Framework For Building Async APIs With Python 3.11+</b> 

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="logo" style="width: 450px">
</p>

<p>
  <img alt="logo" style="width: 50px" src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png">
   <b>Supported by </b><a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">JetBrains</a>
</p>

**_Full Documentation:_** [PantherPy.GitHub.io](https://pantherpy.github.io)

---

### Why Use Panther ?
- Document-oriented Databases ODM ([PantherDB](https://pypi.org/project/pantherdb/), MongoDB)
- Built-in Websocket Support
- Cache APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares
- Handle Custom Throttling 
- Visual API Monitoring (In Terminal)
---


### Benchmark

| Framework  | Throughput (Request/Second) |
|------------|-----------------------------|
| Blacksheep | 5,339                       |
| Muffin     | 5,320                       |
| Panther    | 5,112                       |
| Sanic      | 3,660                       |
| FastAPI    | 3,260                       |
| Tornado    | 2,081                       |
| Bottle     | 2,045                       |
| Django     | 821                         |
| Flask      | 749                         |


> **More Detail:** https://github.com/PantherPy/frameworks-benchmark


---


### Installation
- <details>
    <summary>Create a Virtual Environment</summary>
    <pre>$ python3 -m venv .venv</pre>
  
  </details>
  
- <details>
    <summary>Active The Environment</summary>
    * Linux & Mac
      <pre>$ source .venv/bin/activate</pre>
    * Windows
      <pre>$ .\.venv\Scripts\activate</pre>
  
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
---

### Example

- #### You can create project with
 
    ```console 
    $ panther create myproject
    ``` 
  
- #### or create it yourself:

    **core/configs.py**:
    
    ```python
    URLs = 'core.urls.url_routing'
    ```
    
    **core/urls.py**:
    
    ```python
    from app.urls import urls as app_urls
    
    url_routing = {
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
            'panther_version': version(),
            'datetime_now': datetime.now().isoformat(),
            'user_agent': request.headers.user_agent
        }
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
    ```

- Then **run** the project:
  
  - `$ cd myproject`
  - `$ panther run` or `$ panther run --reload` 
  
  now you can see these two urls:</b>

  * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

  * [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)



> **Writing Your First CRUD: [First CRUD](https://pantherpy.github.io/first_crud)**

---

![roadmap](https://github.com/AliRn76/panther/raw/master/docs/docs/images/roadmap.jpg)

---

### Support

**If you find this project useful, please give it a star ⭐️.**
