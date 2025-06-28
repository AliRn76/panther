## Panther
**A Fast & Friendly Web Framework for Building Async APIs with Python 3.10+**

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="Panther Logo" style="width: 450px">
</p>

[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/)  [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![License](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)

---

## 🐾 Why Choose Panther?

Panther is designed to be **fast**, **simple**, and **powerful**. Here's what makes it special:

- **One of the fastest Python frameworks** available
- **File-based database** ([PantherDB](https://pypi.org/project/pantherdb/)) - No external database setup required
- **Document-oriented ODM** - Supports MongoDB & PantherDB with familiar syntax
- **API caching system** - In-memory and Redis support
- **OpenAPI/Swagger** - Auto-generated API documentation
- **WebSocket support** - Real-time communication out of the box
- **Authentication & Permissions** - Built-in security features
- **Background tasks** - Handle long-running operations
- **Middleware & Throttling** - Extensible and configurable

---

## Benchmark

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/benchmark.png" alt="Benchmark" style="width: 800px">
</p>

[[TechEmpower Benchmark]](https://www.techempower.com/benchmarks/#section=data-r23&l=zijzen-pa7&c=4)

---

## Supported by

<center>
<a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">
<img alt="JetBrains" src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/jb_beam_50x50.png">
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
from panther.openapi.urls import url_routing as openapi_url_routing
from panther.response import Response

class HelloAPI(GenericAPI):
    # Cache responses for 10 seconds
    cache = timedelta(seconds=10)
    
    def get(self):
        current_time = datetime.now().isoformat()
        return Response(
            data={'message': f'Hello from Panther! 🐾 | {current_time}'},
            status_code=status.HTTP_200_OK
        )

# URL routing configuration
url_routing = {
    '/': HelloAPI,
    'swagger/': openapi_url_routing,  # Auto-generated API docs
}

# Create your Panther app
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
        await self.send("Connected to Panther WebSocket!")
    
    async def receive(self, data: str | bytes):
        # Echo back the received message
        await self.send(f"Echo: {data}")

class WebSocketPage(GenericAPI):
    def get(self):
        template = """
        <h2>🐾 Panther WebSocket Echo Server</h2>
        <input id="msg"><button onclick="s.send(msg.value)">Send</button>
        <ul id="log"></ul>
        <script>
            const s = new WebSocket('ws://127.0.0.1:8000/ws');
            s.onmessage = e => log.innerHTML += `<li><- ${msg.value}</li><li>-> ${e.data}</li>`;
        </script>
        """
        return HTMLResponse(template)

url_routing = {
    '': WebSocketPage,
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
