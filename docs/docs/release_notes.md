### 5.0.0
- Support Different `Middlewares` Per API
- Change `path` arg to `name` in `TemplateResponse()`
- Change `new_password` arg to `password` in `BaseUser.check_password()`
- New Style of Middleware declaration [[Doc]](https://...)

### 4.3.6
- Support middleware class in MIDDLEWARES

### 4.3.4
- Cache Response Headers

### 4.3.4
- Fix an issue on TemplateResponse when TEMPLATES_DIR is '.'

### 4.3.3
- Fix not provided context in TemplateResponse

### 4.3.2
- Support `Python 3.13` 

### 4.3.0
- Support `Jinja2 Template Engine` 

### 4.2.0
- Support `OPTIONS` method

### 4.1.3
- Add `reload()` method to queries
- Add `get_input_model()` & `get_output_model()` to `GenericAPI`
- Support `per_delete()` & `post_delete()` in `DeleteAPI` 
- Support mongodb operators in `update(`) & `update_one()`

### 4.1.2
- Fix some issues for `Windows`

### 4.1.1
- Fix an issue in `Response.prepare_data()` when `data` is `Cursor`
- Split `paginate` and `template` in `Pagination`

### 4.1.0
- Support `prepare_response` in `Serializers`
- Rename `objects()` to `cursor()`

### 4.0.1
- Fix an issue in `startup` lifespan

### 4.0.0
- Move `database` and `redis` connections from `MIDDLEWARES` to their own block, `DATABASE` and `REDIS`
- Make `Database` queries `async`
- Make `Redis` queries `async`
- Add `StreamingResponse`
- Add `generics` API classes
- Add `login()` & `logout()` to `JWTAuthentication` and used it in `BaseUser`
- Support `Authentication` & `Authorization` in `Websocket`
- Rename all exceptions suffix from `Exception` to `Error` (https://peps.python.org/pep-0008/#exception-names)
- Support `pantherdb 2.0.0` (`Cursor` Added)
- Remove `watchfiles` from required dependencies
- Support `exclude` and `optional_fields` in `ModelSerializer`
- Minor Improvements

### 3.9.0
- Change the style of `ModelSerializer` usage 

### 3.8.2
- Add `content-type = application/json` header in raise response of `__call__` 

### 3.8.1
- Fix an issue in `_create_pantherdb_session()`

### 3.8.0
- Handle WebSocket connections when we have multiple workers with `multiprocessing.Manager`

### 3.7.0
- Add `ModelSerializer`

### 3.6.0
- Use `observable` pattern for loading database middleware and inheritance of the `Query` class
- Remove `IDType` from the `Model`
- Change `encrypt_password()` method, now uses `scrypt` + `md5` 

### 3.5.1
- Set default behavior of `GenericWebsocket.connect` to ignore the connection (`reject`)

### 3.5.0
- Add `WebsocketTestClient`

### 3.4.0
- Support `WebsocketMiddleware`

### 3.3.2
- Add `content-length` to response header

### 3.3.1
- Check `ruff` installation on startup
- Fix an issue in `routing`

### 3.3.0
- Add Auto Reformat Code

### 3.2.4
- Add all() query
- Add tests for `pantherdb`, `load_configs()`, `status.py`, `Panel`, `multipart`, `request headers`
- Refactor `Headers()` class
- Check `uvloop` installation on `Panther init`
- Minor Improvement

### 3.2.1
- Move `Startup` to `__call__`

### 3.2.0
- Support `Startup` & `Shutdown` Events

### 3.1.5
- Support `Websocket` in the `monitoring` 
- Refactor `collect_all_models()`

### 3.1.4
- Check ws redis connection on the `init`
- Refactor `Monitoring` class and usage
- Improve `logging` config
- Check database connection before query

### 3.1.3
- Add `Image` base class 
- Add `size` to `File` base class
- Improve the way of loading `configs` in `single-file` structure
- Improve `background_tasks.py`, `generate_ws_connection_id()`
- `bpython` removed from being the default python shell
- Improve `load_middlewares()` error handling 
- Print `configs` on the `run`
- Add `requirements.txt` for development 
- Update `roadmap.jpg`, `README.md`
 
### 3.1.2
- Add new methods to `BackgroundTask`
  - `every_seconds()`
  - `every_minutes()`
  - `every_hours()`
  - `every_days()`
  - `every_weeks()`
  - `at()`

### 3.1.1
- Upgrade `PantherDB` version
- Add `first()`, `last()` queries

### 3.1.0
- Add `BackgroundTasks`

### 3.0.3
- Add `find_one_or_raise` query
- Add `last_login` to `BaseUser`
- Add `refresh_life_time` to `JWTConfig`
- Add `encode_refresh_token()` to `JWTAuthentication`
- Add `encrypt_password()`
- Handle `PantherException`
- Handle `RedisConnection` without `connection_pool`

### 3.0.2
- Added 'utf-8' encoding while opening the file "README.md" in setup.py
- Fixed panther shell not working issue in windows.
- Added a condition to raise error if no argument is passed to panther command in cli.

### 3.0.1
- Assume content-type is 'application/json' if it was empty
- Fix an issue on creating instance of model when query is done

### 3.0.0
- Support **Websocket**
- Implement **Built-in TestClient**
- Support Single-File Structure
- Support `bytes` as `Response.data`
- Add `methods` to `API()`
- Change `Request.pure_data` to `Request.data`
- Change `Request.data` to `Request.validated_data`
- Change `panther.middlewares.db.Middleware` to `panther.middlewares.db.DatabaseMiddleware`
- Change `panther.middlewares.redis.Middleware` to `panther.middlewares.redis.RedisMiddleware`
- Fix `panther run` command
- Minor Improvement

### 2.4.2
- Don't log content-type when it's not supported

### 2.4.1
- Fix an issue in collect_all_models() in Windows

### 2.4.0
- Handle Complex Multipart-FormData

### 2.3.3
- Fix a bug in response headers

### 2.3.2
- Fix a bug in Template

### 2.3.1
- Handle PlainTextResponse
- Handle Custom Header in Response
- Change the way of accepting 'URLs' in configs (relative -> dotted)
- Fix an issue in collect_all_models()

### 2.3.0
- Handle HTMLResponse

### 2.2.0
- Supporting File 

### 2.1.6
- Fix validation errors on nested inputs

### 2.1.5
- Fix response of nested Models in _panel/<index>/

### 2.1.4
- Add access-control-allow-origin to response header

### 2.1.3
- Upgrade greenlet version in requirements for python3.12

### 2.1.2
- Add ruff.toml
- Add Coverage to workflows
- Fix a bug for running in Windows

### 2.1.1
- Fix a bug in main.py imports

### 2.1.0
- Support Sync APIs

### 2.0.0
- Supporting class-base APIs

### 1.7.20
- Fix an issue in find_endpoint()

### 1.7.19
- Fix an issue in routing
- Fix an issue on return complex dict Response

### 1.7.18
- Remove uvloop from requirements for now (we had issue in windows)

### 1.7.16
- Trying to fix requirements for windows
- Minor improvement in BaseMongoDBQuery

### 1.7.15
- Fix an issue in handling form-data

### 1.7.14
- Add Cache and Throttling doc to FirstCrud
- Fix an issue in BasePantherDBQuery._merge() 

### 1.7.13
- Hotfix validation of _id in Model()

### 1.7.12
- Fix a bug in routing

### 1.7.11
- Fix an issue in template

### 1.7.10
- Fix a bug in `collect_urls` and rename it to `flatten_urls`
- Add General Tests
- Compatible with python3.10 (Not Tested)
- Working on docs

### 1.7.9
- Working on doc

### 1.7.8
- Fix a bug
- Update docs

### 1.7.8
- Fix a bug
- Update docs

### 1.7.7
- Fix a bug
 
### 1.7.5
- Change the way of raising exception in JWTAuthentication
- Rename User model to BaseUser
- Fix template
 
### 1.7.4
- Crop Logo

### 1.7.3
- Add Throttling Doc
- Fix some issue in Doc

### 1.7.2
- Add Throttling to example
- Customize install_requires in setup.py
- Improve monitoring cli command

### 1.7.1
- Rename db BaseModel to Model 
- Add more docs

### 1.7.0
- Add Throttling

### 1.6.1
- Add AdminPermission

### 1.6.0
- Handle Permissions

### 1.5.2
- Improve Response data serialization
- Fix a bug in JWTAuthentication

### 1.5.1
- Fix error messages

### 1.5.0
- Refactor Mongodb ODM
- Minor Improvement

### 1.4.0
- Add QUERY_LOG

### 1.3.2
- Add Uvicorn to the setup requirements
- Update Readme

### 1.3.1
- Fix a bug in project creation template
- Fix a bug in caching

### 1.3.0
- Add PantherDB to Panther
- Remove tinydb

### 1.2.7
- Fix a bug while using tinydb

### 1.2.6
- Update Readme

### 1.2.5
- Fix install_requires issue
- Add benchmarks to docs

### 1.2.4
- Remove Uvicorn From install_requires
- Working on Docs

### 1.2.3
- Fix URL Routing

### 1.2.1
- Path Variable Handled Successfully

### 1.2.0
- Read multipart/form-data with Regex

### 1.1.9
- Refactoring code style with ruff 
- Add asyncio.TaskGroup() 

### 1.1.8
- Refactor cli run command 

### 1.1.7
- Add benchmark pictures to doc 

### 1.1.5
- Clean Readme
- Clean main.py 

### 1.1.4
- Update Readme 

### 1.1.3
- Fix a query in TinyDB 

### 1.1.2
- Add delete_many query to TinyDB 

### 1.1.1
- Add TinyDB

### 1.1.0
- Debug the Template 

### 1.0.9
- Handle string exceptions (raise them as detail: error) 
- Little debug on MongoQueries

### 1.0.7
- Working on queries
- Fix a bug in query methods 

### 1.0.6
- Update the Template 

### 1.0.4
- Debug template 

### 1.0.2
- Add global config
- Split the BaseModels
- Worked on MongoQuery
- Set Mongo as default database while creating project 
- Minor Improvement

### 1.0.1
- Add alembic To Project 

### 1.0.
- Refactor & Complete the CLI 

### 0.1.9
-  Fix install_requires

### 0.1.8
- Update Readme

### 0.1.7
- Update Readme

### 0.1.6
- Handle Most Types as Data in Response

### 0.1.4
- Working On DB Connection 

### 0.0.1
- Make It Ready For PyPI 

