
## Panther 
#### is a fast &  friendly, web framework for building async APIs with Python 3.11+ 

<hr/>

### Features:
- Document-oriented Databases ORM (TinyDB, MongoDB)
- Visual API Monitoring (In Terminal)
- Cache APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares



### Requirements
```console
Python 3.11+
```

<hr/>

### Installation

- <details>
  <summary>Create a Virtual Environment</summary>
  <pre>$ python -m venv .venv</pre>
  </details>


- <details>
  <summary>Active The Environment</summary></br>
  * Linux & Mac
    <pre>$ source .venv/bin/activate</pre>
  * Windows
    <pre>$ .\.venv\Scripts\activate</pre>   
  </details>


- <details open>
  <summary>Install Panther</summary></br>
  <pre>$ pip install panter</pre>
  or 
  <pre>$ pip install panter[full] # include JWT Authentication</pre>
  </details>

<hr/>

### Usage


- <details open>
  <summary>Create Project</summary>
  <pre>$ panther create &lt;project_name&gt; &lt;directory&gt;</pre>
  </details>


- <details open>
  <summary>Monitoring Requests</summary>
  <pre>$ panther monitor</pre>
  </details>


- <details>
  <summary>Run Project</summary></br>
  Panther needs Uvicorn as ASGI (Asynchronous Server Gateway Interface)
  <pre>$ pip install uvicorn[standard]</pre>
  Then
  <pre>$ panther run </pre>
  </details>


- <details>
  <summary>Python Shell</summary>
  <pre>$ panther shell</pre>
  </details>

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
    from panther.configs import config
    from panther.request import Request
    from panther.response import Response
    
    
    @API()
    async def hello_world():
        return {'detail': 'Hello World'}
    
    
    @API()
    async def info(request: Request):
        data = {
            'version': version(),
            'debug': config['debug'],
            'db_engine': config['db_engine'],
            'default_cache_exp': config['default_cache_exp'],
            'user_agent': request.headers.user_agent,
            'content_length': request.headers.content_length,
        }
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
    ```
    
- #### Then run (`$ panther run`) the project, now you can see these two urls:

  * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

  * [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)



> More examples: [https://github.com/AliRn76/panther/tree/master/example](https://github.com/AliRn76/panther/tree/master/example).
