from panther import Panther
from panther.app import GenericAPI
from panther.db import Model
from panther.response import HTMLResponse
from panther.websocket import GenericWebsocket, send_message_to_websocket


class User(Model):
    connection_id: str


DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': 'database.pdb',
    }
}


class BroadcastWebsocket(GenericWebsocket):
    async def connect(self, **kwargs):
        await self.accept()
        await User.insert_one(connection_id=self.connection_id)

    async def receive(self, data: str | bytes):
        users = await User.find()
        for user in users:
            await send_message_to_websocket(user.connection_id, data)


class MainPage(GenericAPI):
    def get(self):
        template = """
        <input id="msg">
        <button onclick="sendMessage()">Send</button>
        <ul id="log"></ul>
        
        <script>
            const s = new WebSocket('ws://127.0.0.1:8000/ws');
            const log = document.getElementById("log");
            const msgInput = document.getElementById("msg");
        
            function sendMessage() {
                const message = msgInput.value;
                s.send(message);
                log.innerHTML += `<li><b>→</b> ${message}</li>`;
                msgInput.value = '';
            }
        
            s.onmessage = e => {
                log.innerHTML += `<li><b>←</b> ${e.data}</li>`;
            };
        </script>
        """
        return HTMLResponse(template)


url_routing = {
    '': MainPage,
    'ws': BroadcastWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
