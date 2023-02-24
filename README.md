
### Panther 
<b>is a fast &  friendly, web framework for building async APIs with Python 3.11+</b> 

<hr/>

### Features:
- Document-oriented Databases ORM (TinyDB, MongoDB)
- Visual API Monitoring (In Terminal)
- Cache APIs (In Memory, In Redis)
- Built-in Authentication Classes (Customizable)
- Built-in Permission Classes (Customizable)
- Handle Custom Middlewares


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


### TODO:

#### Base 
- [x] Start with Uvicorn 
- [x] Fix URL Routing 
- [x] Read Configs 
- [x] Handle Exceptions 
- [x] Add Custom Logger 
- [x] Request Class 
- [x] Response Class 
- [x] Validate Input 
- [x] Custom Output Model 
- [x] Log Queries
- [x] Add Package Requirements
- [x] Custom Logging
- [x] Caching
- [x] Handle Path Variable
- [x] Handle Form-Data
- [ ] Handle Cookie
- [ ] Handle File 
- [ ] Handle WS 
- [ ] Handle GraphQL
- [ ] Handle Throttling
- [ ] Handle Testing

#### Database:
- [x] Structure Of DB Connection
- [x] TinyDB Connection
- [x] MongoDB Connection
- [x] Create Custom BaseModel For All Type Of Databases
- [ ] Set TinyDB As Default

#### Custom ORM
- [x] Get One 
- [x] List  
- [x] Create 
- [x] Delete 
- [x] Update
- [ ] Get or Raise
- [ ] Get or Create
- [ ] List with Pagination
- [ ] Other Queries In TinyDB
- [ ] Other Queries In MongoDB

#### Middleware
- [x] Add Middlewares To Structure
- [x] Create BaseMiddleware
- [x] Pass Custom Parameters To Middlewares
- [x] Import Custom Middlewares Of User

#### Authentication 
- [x] JWT Authentication
- [x] Separate Auth For Every API
- [ ] Handle Permissions 
- [ ] Token Storage Authentication
- [ ] Cookie Authentication
- [ ] Query Param Authentication
- [ ] Store JWT After Logout In Redis/ Memory

#### Cache
- [x] Add Redis To Structure
- [x] Create Cache Decorator
- [x] Handle In Memory Caching 
- [x] Handle In Redis Caching 
- [ ] Write Async LRU_Caching With TTL (Replace it with in memory ...)


#### CLI
- [x] Create Project 
- [x] Run Project 
- [x] Monitor Requests Response Time
- [x] Create Project with Options
- [x] Monitoring With Textual
    
#### Documentation 
- [x] Create MkDocs For Project 
- [ ] Benchmarks
- [ ] Release Notes
- [ ] Features
- [ ] Complete The MkDoc

#### Tests 
- [ ] Write Test For Panther 
- [ ] Test ...