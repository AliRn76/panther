## Panther 
<b>Is A Fast &  Friendly, Web Framework For Building Async APIs With Python 3.11+</b> 

<p align="center">
<img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo.png" alt="logo" style="width: 200px">
</p>

>_Full Documentation_ -> [https://pantherpy.github.io](https://pantherpy.github.io)
> 
>_PyPI_ -> [https://pypi.org/project/panther/](https://pypi.org/project/panther/)

---

### Why Use Panther ?
- Document-oriented Databases ODM ([PantherDB](https://pypi.org/project/pantherdb/), MongoDB)
- Visual API Monitoring (In Terminal)
- Caching for APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares
- Handle Custom Throttling 
---

### Benchmark
We implemented most of the Python frameworks and sent 
`25,000` requests per second 
for `10` seconds
(Total `250,000` requests)
in the same environment
with [https://github.com/nakabonne/ali](https://github.com/nakabonne/ali) and here's the result:

> you can find the detailed results & source codes here --> [benchmarks](https://pantherpy.github.io/benchmarks/)


| Framework  | Throughput  | Request Handled  | Max Latencies |
|------------|-------------|------------------|---------------|
| Sanic      | 23,326      | 233,842          | 268.8ms       |
| Panther    | 14,719      | 147,595          | 113.1ms       |
| FastAPI    | 14,573      | 146,467          | 155.1ms       |
| Tornado    | 4,969       | 50.585           | 426.5ms       |
| Flask      | 3,555       | 36,396           | 1.2s          |
| Django     | 2,188       | 22,814           | 526.3ms       |
| Bottle     | 1,226       | 39,650           | 30.0s         |
| Pyramid    | 1,023       | 30,912           | 30.0s         |
| Cherrypy   | 639         | 24,944           | 30.0s         |

---

### Installation
- <details>
    <summary>Create a Virtual Environment</summary>
    <pre>$ python -m venv .venv</pre>
  
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
    * Include JWT Authentication
      <pre>$ pip install panther[full]</pre>
  </details>
  
---

### Usage

- #### Create Project

    ```console
    $ panther create <project_name> <directory>
    ```

- #### Run Project
    Panther Uses [Uvicorn](https://github.com/encode/uvicorn) as ASGI (Asynchronous Server Gateway Interface)
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
    
    
    @API()
    async def hello_world():
        return {'detail': 'Hello World'}
    
    
    @API(cache=True, throttling=Throttling(rate=5, duration=timedelta(minutes=1)))
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



> More examples: [https://github.com/AliRn76/panther/tree/master/example](https://github.com/AliRn76/panther/tree/master/example).
