# Panther
<hr/>

## Requirements
<div class="termy">

```console
Python 3.10+
```
</div>

<hr/>

## Installation

- ### Create Virtual Environment

  * <a href="https://">Linux </a>
  * <a href="https://">Windows </a>
  * <a href="https://">Mac </a>

- ### Install Panther 
    <div class="termy">

    ```console
    $ pip install panter
    ```
    </div>
<hr/>

## Usage
- #### Create Project
    <div class="termy">
    
    ```console
    $ panther create
    ```
    </div>
- #### Run Project
    <div class="termy">
    
    ```console
    $ panther run 
    ```
    </div>

<hr>

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
- [ ] Handle Cookie
- [ ] Handle File 
- [ ] Handle Form-Data
- [ ] Handle WS 
- [ ] Handle GraphQL
- [ ] Add py.typed 
- [ ] Add Package Requirements
- [ ] Refactor app __call__ 

#### Database:
- [x] Structure Of DB Connection
- [x] SQLite Connection
- [ ] MySQL Connection
- [ ] PostgreSQL Connection
- [ ] Set SQLite As Default

#### Simple Query
- [x] Get One 
- [x] List  
- [x] Create 
- [x] Delete 
- [x] Update
- [x] Get or Raise
- [x] Get or Create
- [ ] Test Update

#### Middleware
- [x] Add Middlewares To Structure
- [x] Create BaseMiddleware
- [x] Pass Custom Parameters To Middlewares
- [ ] Import Custom Middlewares Of User

#### Authentication 
- [ ] Choose Type of Authentication 
- [ ] JWT 
- [ ] Token Storage 
- [ ] Cookie 
- [ ] Query Param
- [ ] Store JWT After Logout In Redis

#### Cache
- [x] Add Redis To Structure

#### Throttling
- [ ] Monitor Requests 
- [ ] Ban User 
- [ ] User Redis For Block His JWT

#### Migration 
- [x] Add Alembic To Structure
- [ ] Set Custom Name For Migrations 
- [ ] Merge Migrations 

#### TUI (for Linux)
- [ ] Create Project with Options
- [ ] Monitor Requests  
- [ ] Monitor Query Performance (Time)
- [ ] Monitor Response Time
- [ ] Monitor Fastest & Slowest API
- [ ] Migration
- [ ] Monitor Migration Flow
    
#### CLI (for Windows)
- [ ] Create Project 
- [ ] Migration

#### Documentation 
- [ ] Read The Doc or MkDoc 
- [ ] Framework Performance Ranking 

#### Tests 
- [ ] Add Test To Package