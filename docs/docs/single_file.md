# Using Panther in a Single-File Structure

If you prefer to work with `Panther` in a single Python file, follow the steps below to quickly set up and run your API.

## Step 1: Define Your APIs

Write your API endpoints as usual using the `@API()` decorator or inheriting from `GenericAPI`:

```python title="main.py" linenums="1"
from panther.app import API

@API()
async def hello_world_api():
    return {'detail': 'Hello World'}
```

## Step 2: Create a URL Routing Dictionary

Map your endpoints to their respective URLs in a dictionary (commonly named `url_routing`):

```python title="main.py" linenums="6"
url_routing = {
    '/': hello_world_api,
}
```

## Step 3: Initialize the Panther App

Create an instance of the `Panther` app, passing your current module name and the URL routing dictionary:

```python title="main.py" linenums="1"
from panther import Panther
from panther.app import API

@API()
async def hello_world_api():
    return {'detail': 'Hello World'}

url_routing = {
    '/': hello_world_api,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
```

## Step 4: Run Your Project

Use the following command to start your application:

```bash
panther run main:app
```

---

## Additional Notes

- The `urls` parameter is required unless you provide the URLs via configuration.
- When you pass `configs=__name__` to the `Panther` constructor, Panther will load the configuration from the current file. If you omit this, Panther defaults to loading configuration from `core/configs.py`.
