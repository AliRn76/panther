
## Panther 
<b>Is A Fast &  Friendly, Web Framework For Building Async APIs With Python 3.11+</b> 

<hr/>

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
`2_000` requests per second 
for a total of `10` seconds
(Total `200_000` requeusts)
in the same environment
with [https://github.com/nakabonne/ali](https://github.com/nakabonne/ali) and here's the result:

> we won't rate other frameworks with throughput, so the names are censored.

| Framework   | Request Handled |
|-------------|-----------------|
| Framework 1 | x               |
| Panther     | x               |
| Framework 2 | x               |
| Framework 3 | x               |
| Framework 4 | x               |
| Framework 5 | x               |
| Framework 6 | x               |
| Framework 7 | x               |

test source codes: [here](https://pantherpy.github.io/benchmark/codes)
---

### Installation

- #### Create a Virtual Environment
  ```console
  $ python -m venv .venv
  ```

- #### Active The Environment
    * Linux & Mac
    ```console
    $ source .venv/bin/activate
    ```
    * Windows
    ```console
    $ .\.venv\Scripts\activate
    ```

- #### Install Panther
  ```console
  $ pip install panter
  ```
    or
    ```console
    $ pip install panter[full] # include JWT Authentication
    ```

<hr/>

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
