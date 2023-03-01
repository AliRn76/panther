
## Panther 
<b>Is A Fast &  Friendly, Web Framework For Building Async APIs With Python 3.11+</b> 

>_Full Documentation_ -> [https://pantherpy.github.io](https://pantherpy.github.io)
> 
>_PyPI_ -> [https://pypi.org/project/panther/](https://pypi.org/project/panther/)

---

### Features
- Document-oriented Databases ORM (TinyDB, MongoDB)
- Visual API Monitoring (In Terminal)
- Cache APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares
---

### Benchmark
We implemented most of the Python frameworks and sent 
`60_000` requests per second 
for a total of `10` seconds
(Total `600_000` requests)
in the same environment
with [https://github.com/nakabonne/ali](https://github.com/nakabonne/ali) and here's the result:

> we won't rate other frameworks with throughput, so the names are censored.
> but you can find the detailed results & source codes [[here]](https://pantherpy.github.io/benchmark/codes)


| Framework | Request Handled | Max Latencies |
|-----------|-----------------|---------------|
| ...       | 275,060         | 270.3ms       |
| ...       | 188,016         | 195.6ms       |
| Panther   | 156,743         | 214.7ms       |
| ...       | 66,274          | 476.2ms       |
| ...       | 52,350          | 1.2924s       |
| ...       | 32,944          | 30.00ms       |
| ...       | 31,336          | 30.03ms       |
| ...       | 19,820          | 30.0s         |

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
  Panther needs Uvicorn as ASGI (Asynchronous Server Gateway Interface)
  ```console
  $ pip install uvicorn[standard]
  ```
  Then
  ```console
  $ panther run 
  ```

- #### Monitoring Requests

    ```console
    $ panther monitor 
    ```

- #### Python Shell
 
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
    from panther import version, status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response
    
    
    @API()
    async def hello_world():
        return {'detail': 'Hello World'}
    
    
    @API()
    async def info(request: Request):
        data = {
            'version': version(),
            'user_agent': request.headers.user_agent,
            'content_length': request.headers.content_length,
        }
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
    ```

- <b> Then run (`$ panther run`) the project, now you can see these two urls:</b>

  * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

  * [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)



> More examples: [https://github.com/AliRn76/panther/tree/master/example](https://github.com/AliRn76/panther/tree/master/example).
