## Panther
**A Fast & Friendly Web Framework for Building Async APIs with Python 3.10+**

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="Panther Logo" style="width: 450px">
</p>

<center>

[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![License](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)

</center>

---

## Why Choose Panther?
- One of the **fastest Python frameworks** available
- Built-in **file-based** database ([PantherDB](https://pypi.org/project/pantherdb/))
- Built-in document-oriented database **ODM** (Supports **MongoDB** & PantherDB)
- Built-in API **caching** system (Supports in-memory & **Redis**)
- Built-in support of **OpenAPI** (swagger)
- Built-in **Admin Panel**
- Native **WebSocket** support
- Integrated **authentication** classes
- Built-in **permission** handling
- Supports custom **background tasks**, **middlewares**, and **throttling**
- Offers both **function-based** and **class-based** APIs
- Real-time API **monitoring** in the terminal

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

1. **Create a Virtual Environment**

   ```shell
   $ python3 -m venv .venv
   ```

2. **Activate the Environment**

   - **Linux & Mac**
     ```shell
     $ source .venv/bin/activate
     ```
   - **Windows**
     ```shell
     $ .\.venv\Scripts\activate
     ```

3. **Install Panther**

   - Standard installation:
     ```shell
     $ pip install panther
     ```
   - Full installation (includes MongoDB, JWTAuth, Ruff, Redis, Websockets, Cryptography, IPython):
     ```shell
     $ pip install panther[full]
     ```

---

## Getting Started

### Create a New Project
```shell
$ panther create
```

### Run the Project
```shell
$ panther run --reload
```
_Panther uses [Uvicorn](https://github.com/encode/uvicorn) as the default ASGI server, but you can also use [Granian](https://pypi.org/project/granian/), [Daphne](https://pypi.org/project/daphne/), or any ASGI-compatible server._

### Monitor API Requests
```shell
$ panther monitor
```

### Open a Python Shell
```shell
$ panther shell main.py  # Replace main.py with your application file name
```

---

## API Example

Create a `main.py` file:

```python
from datetime import datetime, timedelta
from panther import status, Panther
from panther.app import GenericAPI
from panther.response import Response

class FirstAPI(GenericAPI):
    # Enable caching for 10 seconds
    cache = True
    cache_exp_time = timedelta(seconds=10)

    def get(self):
        date_time = datetime.now().isoformat()
        data = {'detail': f'Hello World | {date_time}'}
        return Response(data=data, status_code=status.HTTP_202_ACCEPTED)

url_routing = {'': FirstAPI}
app = Panther(__name__, configs=__name__, urls=url_routing)
```

Run the project:
```shell
$ panther run --reload
```
Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## WebSocket Example

Create a `main.py` file:

```python
from panther import Panther
from panther.app import GenericAPI
from panther.response import HTMLResponse
from panther.websocket import GenericWebsocket

class EchoWebsocket(GenericWebsocket):
    async def connect(self, **kwargs):
        await self.accept()

    async def receive(self, data: str | bytes):
        # Echo message to client itself
        await self.send(data)

class MainPage(GenericAPI):
    def get(self):
        template = """
        <input type="text" id="messageInput">
        <button id="sendButton">Send Message</button>
        <ul id="messages"></ul>
        <script>
            var socket = new WebSocket('ws://127.0.0.1:8000/ws');
            socket.addEventListener('message', function (event) {
                var li = document.createElement('li');
                document.getElementById('messages').appendChild(li).textContent = 'Server: ' + event.data;
            });
            function sendMessage() {
                socket.send(document.getElementById('messageInput').value);
            }
            document.getElementById('sendButton').addEventListener('click', sendMessage);
        </script>
        """
        return HTMLResponse(template)

url_routing = {
    '': MainPage,
    'ws': EchoWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
```

Run the project:
```shell
$ panther run --reload
```
Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and interact with WebSockets.