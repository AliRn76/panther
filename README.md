
[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![license](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)


## Panther 
<b>Is A Fast &  Friendly Web Framework For Building Async APIs With Python 3.10+</b> 

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="logo" style="width: 450px">
</p>

**_📚 Full Documentation:_** [PantherPy.GitHub.io](https://pantherpy.github.io)

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

### Supported by
<center>
    <a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">
      <img alt="jetbrains" src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/jb_beam_50x50.png">
    </a>
</center>

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


> **More Detail:** https://GitHub.com/PantherPy/frameworks-benchmark

---

### Installation
- <details>
    <summary>1. Create a Virtual Environment</summary>
    <pre>$ python3 -m venv .venv</pre>
  
  </details>
  
- <details>
    <summary>2. Active The Environment</summary>
    * Linux & Mac
      <pre>$ source .venv/bin/activate</pre>
    * Windows
      <pre>$ .\.venv\Scripts\activate</pre>
  
  </details>

- <details open>
    <summary>3. <b>Install Panther</b></summary>
    - ⬇ Normal Installation
      <pre><b>$ pip install panther</b></pre>
    -  ⬇ Include full requirements (MongoDB, JWTAuth, Ruff, Redis, bpython)
      <pre>$ pip install panther[full]</pre>
  </details>
  
---

### Usage

- #### Create Project

    ```console
    $ panther create
    ```

- #### Run Project
    
    ```console
    $ panther run --reload
    ```
  _* Panther uses [Uvicorn](https://github.com/encode/uvicorn) as ASGI (Asynchronous Server Gateway Interface) but you can run the project with [Granian](https://pypi.org/project/granian/), [daphne](https://pypi.org/project/daphne/) or any ASGI server too_

- #### Monitoring Requests

    ```console
    $ panther monitor 
    ```

- #### Python Shell

    ```console
    $ panther shell
    ```
  
---

### Single-File Structure Example
  - Create `main.py`

    ```python
    from datetime import datetime, timedelta
    
    from panther import version, status, Panther
    from panther.app import API
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
    
    
    url_routing = {
        '': hello_world,
        'info': info,
    }
    
    app = Panther(__name__, configs=__name__, urls=url_routing)
    ```

  - Run the project:
    - `$ panther run --reload` 
  

  - Now you can see these two urls:</b>
    - [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    - [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)



> **Next Step: [First CRUD](https://pantherpy.github.io/function_first_crud)**

> **Real Word Example: [Https://GitHub.com/PantherPy/panther-example](https://GitHub.com/PantherPy/panther-example)**

---

### Roadmap

![roadmap](https://raw.githubusercontent.com/AliRn76/panther/master/docs/docs/images/roadmap.jpg)

---

**If you find this project useful, please give it a star ⭐️.**
