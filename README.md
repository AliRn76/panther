# Panther
<hr/>

## Requirements
```console
Python 3.11+
```

<hr/>

## Installation

- ### Create Virtual Environment

    ```concole
    $ python -m venv .venv
    ```

- ### Active The Environment

    * Linux & Mac
      ```concole
      $ source .venv/bin/activate
      ```
      
    * Windows
      ```concole
      $ .\.venv\Scripts\activate
      ```

- ### Install Panther

    ```console
    $ pip install panter
    ```
<hr/>

## Usage
- #### Create Project

    ```console
    $ panther create <project_name> <directory>
    ```

- #### Run Project

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

## TODO:

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
- [ ] Handle Path Variable
- [ ] Handle Form-Data
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
- [x] Monitoring
- [ ] Complete The CLI With Textual ...
    
#### Documentation 
- [x] Create MkDocs For Project 
- [ ] Benchmarks
- [ ] Release Notes
- [ ] Features
- [ ] Complete The MkDoc

#### Tests 
- [ ] Write Test For Panther 
- [ ] Test ...