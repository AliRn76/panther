
[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![license](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)


## Panther 
<b>Is A Fast &  Friendly Web Framework For Building Async APIs With Python 3.10+</b> 

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="logo" style="width: 450px">
</p>

**_📚 Full Documentation:_** [PantherPy.GitHub.io](https://pantherpy.github.io)

---

## Why Choose Panther?
- One of the **Fastest Python Frameworks** available
- Built-in **File-Based** database ([PantherDB](https://pypi.org/project/pantherdb/))
- Built-in document-oriented database **ODM** (Supports **MongoDB** & PantherDB)
- Built-in API **Caching** system (Supports in-memory & **Redis**)
- Built-in support of **OpenAPI** (swagger)
- Native **WebSocket** support
- Integrated **Authentication** classes
- Built-in **Permission** handling
- Supports custom **Background Tasks**, **middlewares**, and **throttling**
- Offers both **Function-Based** and **Class-Based** APIs
- Real-time API **Monitoring** in the terminal

---

### Supported by
<center>
    <a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">
      <img alt="jetbrains" src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/jb_beam_50x50.png">
    </a>
</center>

---

## Installation

   ```shell
   $ pip install panther
   ```

---


## Getting Started

### Quick Start Guide

1. **Create a new project directory**
   ```shell
   $ mkdir my_panther_app
   $ cd my_panther_app
   ```

2. **Set up your environment**
   ```shell
   $ python3 -m venv .venv
   $ source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   $ pip install panther
   ```

3. **Create your first application**
    
    Create a `main.py` file with one of the examples below.

### Basic API Example

Here's a simple REST API endpoint that returns a "Hello World" message:

```python title="main.py" linenums="1"
from datetime import datetime, timedelta

from panther import status, Panther
from panther.app import GenericAPI
from panther.openapi.urls import urls as openapi_urls
from panther.response import Response


class FirstAPI(GenericAPI):
    # Response will be cached for 10 seconds for each user/ ip
    cache = timedelta(seconds=10)

    def get(self):
        current = datetime.now().isoformat()
        data = {'detail': f'Hello World | {current}'}
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)


url_routing = {
    '/': FirstAPI,
    'swagger/': openapi_urls,  # Auto generated Swagger API documentation
}
app = Panther(__name__, configs=__name__, urls=url_routing)
```

### WebSocket Example

Here's a simple WebSocket echo server that sends back any message it receives:

```python title="main.py" linenums="1"
from panther import Panther
from panther.app import GenericAPI
from panther.response import HTMLResponse
from panther.websocket import GenericWebsocket

class EchoWebsocket(GenericWebsocket):
    async def connect(self, **kwargs):
        await self.accept()

    async def receive(self, data: str | bytes):
        await self.send(data)

class MainPage(GenericAPI):
    def get(self):
        template = """
        <input id="msg"><button onclick="s.send(msg.value)">Send</button>
        <ul id="log"></ul>
        <script>
            const s = new WebSocket('ws://127.0.0.1:8000/ws');
            s.onmessage = e => log.innerHTML += `<li><- ${msg.value}</li><li>-> ${e.data}</li>`;
        </script>
        """
        return HTMLResponse(template)

url_routing = {
    '': MainPage,
    'ws': EchoWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
```

### Running Your Application

1. **Start the development server**
   ```shell
   $ panther run main:app --reload
   ```
   
    > **Note:** Panther uses [Uvicorn](https://github.com/encode/uvicorn) as the default ASGI server, but you can also use [Granian](https://pypi.org/project/granian/), [Daphne](https://pypi.org/project/daphne/), or any ASGI-compatible server.

2. **Test your application**
    - For the _API_ example: Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to see the "Hello World" response
    - For the _WebSocket_ example: Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and send a message. 

---
**📚 Full Documentation:** [PantherPy.GitHub.io](https://pantherpy.github.io)

**⭐️ If you find this project useful, don't forget to give it a star :).**
