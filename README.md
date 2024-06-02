
[![PyPI](https://img.shields.io/pypi/v/panther?label=PyPI)](https://pypi.org/project/panther/) [![PyVersion](https://img.shields.io/pypi/pyversions/panther.svg)](https://pypi.org/project/panther/) [![codecov](https://codecov.io/github/AliRn76/panther/graph/badge.svg?token=YWFQA43GSP)](https://codecov.io/github/AliRn76/panther) [![Downloads](https://static.pepy.tech/badge/panther/month)](https://pepy.tech/project/panther) [![license](https://img.shields.io/github/license/alirn76/panther.svg)](https://github.com/alirn76/panther/blob/main/LICENSE)


## Panther 
<b>Is A Fast &  Friendly Web Framework For Building Async APIs With Python 3.10+</b> 

<p align="center">
  <img src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/logo-vertical.png" alt="logo" style="width: 450px">
</p>

**_📚 Full Documentation:_** [PantherPy.GitHub.io](https://pantherpy.github.io)

---

### Why Use Panther ?
- Include Simple **File-Base** Database ([PantherDB](https://pypi.org/project/pantherdb/))
- Built-in Document-oriented Databases **ODM** (**MongoDB**, PantherDB)
- Built-in **Websocket** Support
- Built-in API **Caching** System (In Memory, **Redis**)
- Built-in **Authentication** Classes
- Built-in **Permission** Classes
- Built-in Visual API **Monitoring** (In Terminal)
- Support Custom **Background Tasks**
- Support Custom **Middlewares**
- Support Custom **Throttling**
- Support **Function-Base** and **Class-Base** APIs
- It's One Of The **Fastest Python Framework** ([Benchmark](https://www.techempower.com/benchmarks/#section=test&runid=d3364379-1bf7-465f-bcb1-e9c65b4840f9&hw=ph&test=fortune&l=zik0zj-6bi))
---

### Supported by
<center>
    <a href="https://drive.google.com/file/d/17xe1hicIiRF7SQ-clg9SETdc19SktCbV/view?usp=sharing">
      <img alt="jetbrains" src="https://github.com/AliRn76/panther/raw/master/docs/docs/images/jb_beam_50x50.png">
    </a>
</center>

---

### Installation
```shell
$ pip install panther
```

### Usage

- #### Create Project

    ```shell
    $ panther create
    ```

- #### Run Project
    
    ```shell
    $ panther run --reload
    ```
  _* Panther uses [Uvicorn](https://github.com/encode/uvicorn) as ASGI (Asynchronous Server Gateway Interface) but you can run the project with [Granian](https://pypi.org/project/granian/), [daphne](https://pypi.org/project/daphne/) or any ASGI server_

- #### Monitoring Requests

    ```shell
    $ panther monitor 
    ```

- #### Python Shell

    ```shell
    $ panther shell
    ```
  
---

### API Example
  - Create `main.py`

    ```python
    from datetime import datetime, timedelta
    
    from panther import status, Panther
    from panther.app import GenericAPI
    from panther.response import Response
    
    
    class FirstAPI(GenericAPI):
        # Cache Response For 10 Seconds
        cache = True
        cache_exp_time = timedelta(seconds=10)
        
        def get(self):
            date_time = datetime.now().isoformat()
            data = {'detail': f'Hello World | {date_time}'}
            return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
    
    
    url_routing = {'': FirstAPI}
    app = Panther(__name__, configs=__name__, urls=url_routing)
    ```

  - Run the project:
    - `$ panther run --reload` 
  
  - Checkout the [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### WebSocket Echo Example 
  - Create `main.py`

    ```python
    from panther import Panther
    from panther.app import GenericAPI
    from panther.response import HTMLResponse
    from panther.websocket import GenericWebsocket
    
    
    class FirstWebsocket(GenericWebsocket):
        async def connect(self, **kwargs):
            await self.accept()
    
        async def receive(self, data: str | bytes):
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
        'ws': FirstWebsocket,
    }
    app = Panther(__name__, configs=__name__, urls=url_routing)

    ```

  - Run the project:
    - `$ panther run --reload` 
  - Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and work with your `websocket`



> **Next Step: [First CRUD](https://pantherpy.github.io/function_first_crud)**

---

### How Panther Works!

![diagram](https://raw.githubusercontent.com/AliRn76/panther/master/docs/docs/images/diagram.png)

---

### Roadmap

![roadmap](https://raw.githubusercontent.com/AliRn76/panther/master/docs/docs/images/roadmap.jpg)

---

**If you find this project useful, please give it a star ⭐️.**
