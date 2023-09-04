If you want to work with `Panther` in a single-file structure, follow the steps below.

## Steps

1.  Create your file (ex: `main.py`)
2.  Create `app` and pass the current `module` as `configs` to it.

    ```python
    import sys
    from panther import Panther
    
    app = Panther(__name__, configs=sys.modules[__name__])
    ```
    
3.  Define a `URLs` which is pointing to `urls dict`(ex: `url_routing`) of `main.py`.
    ```python
    URLs = 'main.url_routing'
    ```

4.  Write your `APIs` as you like.
5.  Add your `APIs` to your `urls dict` (ex: `url_routing`)
    ```python
    url_routing = {
        ...
    }
    ```

## Example

```python
import sys
from datetime import datetime

from panther import Panther, status, version
from panther.app import API
from panther.configs import config
from panther.request import Request
from panther.response import Response

URLs = 'main.url_routing'


@API()
async def hello_world_api():
    return {'detail': 'Hello World'}


@API()
async def info_api(request: Request):
    data = {
        'version': version(),
        'datetime_now': datetime.now().isoformat(),
        'user_agent': request.headers.user_agent,
        'db_engine': config['db_engine'],
    }
    return Response(data=data, status_code=status.HTTP_202_ACCEPTED)


url_routing = {
    '/': hello_world_api,
    'info/': info_api,
}

app = Panther(__name__, configs=sys.modules[__name__])

```