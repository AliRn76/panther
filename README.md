[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![license](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)

<div align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="Panther Logo" width="450">
  
  # Panther 
  
  **A Fast & Friendly Web Framework for Building Async APIs with Python 3.10+**
  
  [📚 Documentation](https://pantherpy.github.io)
</div>

---

## 🐾 Why Choose Panther?

Panther is designed to be **fast**, **simple**, and **powerful**. Here's what makes it special:

- **One of the fastest Python frameworks** available ([Benchmark](https://www.techempower.com/benchmarks/#section=data-r23&l=zijzen-pa7&c=4))
- **File-based database** ([PantherDB](https://pypi.org/project/pantherdb/)) - No external database setup required
- **Document-oriented ODM** - Supports MongoDB & PantherDB with familiar syntax
- **API caching system** - In-memory and Redis support
- **OpenAPI** - Auto-generated API documentation with multiple UI options
- **WebSocket support** - Real-time communication out of the box
- **Authentication & Permissions** - Built-in security features
- **Background tasks** - Handle long-running operations
- **Middleware & Throttling** - Extensible and configurable
- **Optional Rust web server** - Serve on [hyper](https://hyper.rs) + [tokio](https://tokio.rs) instead of Uvicorn ([docs](https://pantherpy.github.io/rust_server/))

---

## Quick Start

### Installation

```bash
pip install panther
```

- Create a `main.py` file with one of the examples below.

### Your First API

Here's a simple REST API endpoint that returns a "Hello World" message:

```python
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
    'docs/': openapi_url_routing,  # Auto-generated API docs
}

# Create your Panther app
app = Panther(__name__, configs=__name__, urls=url_routing)
```

### WebSocket Echo Server

Here's a simple WebSocket echo server that sends back any message it receives:

```python
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

### Run Your Application

1. **Start the development server**
   ```shell
   $ panther run main:app
   ```
   
2. **Test your application**
    - For the _API_ example: Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to see the "Hello World" response
    - For the _WebSocket_ example: Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and send a message.

### Optional: Run on the Rust Web Server

`panther run` uses Uvicorn by default. Panther also ships an optional web server written in Rust
(hyper + tokio, bridged with PyO3) that speaks the same ASGI protocol:

```shell
$ pip install panther[rust]
$ panther run --server rust main:app
```

Nothing else changes — your APIs, WebSockets and lifespan events behave exactly the same.
See the [Rust Web Server](https://pantherpy.github.io/rust_server/) docs for options and limitations.

---

## For LLMs and Coding Agents

Start with:

- [`AGENTS.md`](AGENTS.md)
- [`docs/llms.txt`](docs/llms.txt)
- [`docs/docs/llm-context.md`](docs/docs/llm-context.md)
- [`examples/canonical/`](examples/canonical/)

These files are kept focused on current Panther APIs and copyable examples.

---

## 🙏 Acknowledgments

<div align="center">
  <p>Supported by</p>
  <a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">
    <img alt="JetBrains" src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/jb_beam_50x50.png">
  </a>
</div>

---

<div align="center">
  <p>⭐️ If you find Panther useful, please give it a star!</p>
</div>
