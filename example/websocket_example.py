from panther import Panther, status
from panther.app import GenericAPI
from panther.middlewares.monitoring import MonitoringMiddleware, WebsocketMonitoringMiddleware
from panther.response import HTMLResponse, Response
from panther.websocket import GenericWebsocket, close_websocket_connection, send_message_to_websocket


class FirstWebsocket(GenericWebsocket):
    async def connect(self, **kwargs):
        await self.accept()

    async def receive(self, data: str | bytes):
        print(f'Received: {data}')
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


class AdminAPI(GenericAPI):
    # curl http://127.0.0.1:8000/admin/01HQ40RAXGJEPPYXJ4X4E7Z7H7/false
    async def get(self, connection_id: str, disconnect: bool):
        if disconnect:
            await close_websocket_connection(connection_id=connection_id, reason="I'm Sorry Your Time Is Up")
        else:
            await send_message_to_websocket(connection_id=connection_id, data='Is Everything Ok?')
        return Response(status_code=status.HTTP_202_ACCEPTED)


MIDDLEWARES = [MonitoringMiddleware, WebsocketMonitoringMiddleware]
url_routing = {
    '': MainPage,
    'admin/<connection_id>/<disconnect>': AdminAPI,
    'ws': FirstWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
