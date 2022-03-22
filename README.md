# Panther
<hr/>

## Requirements

Python 3.10+
<hr/>

## Installation

### Create Virtual Environment

* <a href="https://">Linux </a>
* <a href="https://">Windows </a>
* <a href="https://">Mac </a>

### Install Panther 

<div class="termy">

```console
$ pip install panter
```
</div>
<hr/>

## Usage
#### Create Project
<div class="termy">

```console
$ panther create
```
</div>

#### Manage Project
<div class="termy">

```console
$ panther manage
```
</div>

#### Run Project
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
- [ ] Add py.typed 

#### Database Connection:

- [x] SQLite Connection
- [ ] MySQL Connection
- [ ] PostgreSQL Connection

#### Simple Query
- [x] Get One 
- [x] List  
- [ ] List with Limit & Offset
- [x] Create 
- [x] Delete 
- [ ] Update
- [ ] Get or Raise
- [ ] Get or Create

#### Middleware
- [x] Add Middlewares To Structure
- [x] Create BaseMiddleware

#### Authentication 
- [ ] Choose Type of Authentication 
- [ ] JWT 
- [ ] Token Storage 
- [ ] Cookie 
- [ ] Query Param
- [ ] Store JWT After Logout In Redis

#### Cache
- [ ] Add Redis To Structure

#### Throttling
- [ ] Monitor Requests 
- [ ] Ban User 
- [ ] User Redis For Block His JWT

#### Migration 
- [x] Add Alembic To Structure

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
