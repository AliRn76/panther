
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

---

### Why Use Panther?
- Document-oriented Databases ODM ([PantherDB](https://pypi.org/project/pantherdb/), MongoDB)
- Visual API Monitoring (In Terminal)
- Caching for APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares
- Handle Custom Throttling 
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
---

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


  
> **Writing Your First CRUD: [First CRUD](https://pantherpy.github.io/first_crud)**

---


**<details>
    <summary>TODOs**</summary>

- <details>
    <summary>Base</summary>
  
    - &#x2705; Start with Uvicorn
    - &#x2705; Fix URL Routing
    - &#x2705; Read Configs
    - &#x2705; Handle Exceptions
    - &#x2705; Add Custom Logger
    - &#x2705; Request Class
    - &#x2705; Response Class 
    - &#x2705; Validate Input 
    - &#x2705; Custom Output Model 
    - &#x2705; Log Queries
    - &#x2705; Add Package Requirements
    - &#x2705; Custom Logging
    - &#x2705; Caching
    - &#x2705; Handle Path Variable
    - &#x2705; Handle Simple Form-Data
    - &#x2705; Handle Throttling
    - &#9744; Handle Complex Form-Data
    - &#9744; Handle File 
    - &#9744; Handle Cookie
    - &#9744; Handle WS 
    - &#9744; Handle GraphQL
    - &#9744; Handle Testing
    - &#9744; Generate Swagger For APIs
    - &#9744; Handle ClassBase APIs
  
  </details>

- <details>
    <summary>Database</summary>
  
    - &#x2705; Structure Of DB Connection
    - &#x2705; PantherDB Connection
    - &#x2705; MongoDB Connection
    - &#x2705; Create Custom BaseModel For All Type Of Databases
    - &#x2705; Set PantherDB As Default
  
  </details>

- <details>
    <summary>Custom ODM</summary>

    - &#x2705; Find One
    - &#x2705; Find 
    - &#x2705; Last
    - &#x2705; Count
    - &#x2705; Insert One 
    - &#x2705; Insert Many 
    - &#x2705; Delete One
    - &#x2705; Delete Many
    - &#x2705; Delete Itself
    - &#x2705; Update One
    - &#x2705; Update Many
    - &#x2705; Update Itself
    - &#x2705; Find or Insert
    - &#x2705; Save
    - &#9744; Find or Raise
    - &#9744; Find with Pagination
    - &#9744; Aggregation
    - &#9744; Complex Pipelines
    - &#9744; ...
    
  </details>

- <details>
    <summary>Middleware</summary>
  
    - &#x2705; Add Middlewares To Structure
    - &#x2705; Create BaseMiddleware
    - &#x2705; Pass Custom Parameters To Middlewares
    - &#x2705; Handle Custom Middlewares
  </details>

- <details>
    <summary>Authentication</summary>

    - &#x2705; JWT Authentication
    - &#x2705; Separate Auth For Every API
    - &#x2705; Handle Permissions 
    - &#9744; Token Storage Authentication
    - &#9744; Cookie Authentication
    - &#9744; Query Param Authentication
    - &#9744; Store JWT After Logout In Redis/ Memory
  
  </details>

- <details>
    <summary>Cache</summary>

    - &#x2705; Add Redis To Structure
    - &#x2705; Create Cache Decorator
    - &#x2705; Handle In-Memory Caching 
    - &#x2705; Handle In Redis Caching 
    - &#9744; Write Async LRU_Caching With TTL (Replace it with in-memory ...)
  
  </details>

- <details>
    <summary>CLI</summary>

    - &#x2705; Create Project 
    - &#x2705; Run Project 
    - &#x2705; Create Project with Options
    - &#x2705; Monitoring With Textual
    - &#x2705; Monitor Requests, Response & Time
  
  </details>

- <details>
    <summary>Documentation</summary>

    - &#x2705; Create MkDocs For Project 
    - &#x2705; Benchmarks
    - &#x2705; Release Notes
    - &#x2705; Features
    - &#9744; Complete The MkDoc
  
  </details>

- <details>
    <summary>Tests</summary>

    - &#x2705; Start Writing Tests For Panther 
    - &#9744; Test Client
  
  </details>

</details>


---

### Support

**If you find this project useful, please give it a star ⭐️.**