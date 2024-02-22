from panther import Panther, status
from panther.app import GenericAPI
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
        <html lang="en">
        <head>
            <meta charSet="UTF-8"/>
            <title>Simple WebSocket Example</title>
        </head>
        <body>
        <button id="sendButton">Send Message</button>
        <input type="text" id="messageInput" placeholder="Type your message here"/>
        <ul id="messages"></ul>
        <script>
            var socket;
            
            function connect() {
                socket = new WebSocket('ws://127.0.0.1:8000/ws');
            
                // Connection opened
                socket.addEventListener('open', function (event) {
                    console.log('WebSocket is connected.');
                    document.getElementById('connectButton').disabled = true;
                    document.getElementById('sendButton').disabled = false;
                });
            
                // Listen for messages
                socket.addEventListener('message', function (event) {
                    console.log('Message from server: ', event.data);
                    var messages = document.getElementById('messages');
                    var li = document.createElement('li');
                    li.textContent = 'Server: ' + event.data;
                    messages.appendChild(li);
                });
            
                // Connection closed
                socket.addEventListener('close', function (event) {
                    console.log('WebSocket is closed.');
                    document.getElementById('connectButton').disabled = false;
                    document.getElementById('sendButton').disabled = true;
                });
            
                // Connection error
                socket.addEventListener('error', function (event) {
                    console.log('WebSocket error: ', event);
                });
            }
            
            // Send a message to the server
            function sendMessage() {
                var message = document.getElementById('messageInput').value;
                if (message) {
                    socket.send(message);
                    console.log('Message sent: ', message);
                    var messages = document.getElementById('messages');
                    var li = document.createElement('li');
                    li.textContent = 'Client: ' + message;
                    messages.appendChild(li);
                    document.getElementById('messageInput').value = '';
                }
            }
            
            // Add event listeners to the buttons
            document.getElementById('connectButton').addEventListener('click', connect);
            document.getElementById('sendButton').addEventListener('click', sendMessage);
        </script>
        </body>
        </html>
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


url_routing = {
    '': MainPage,
    'admin/<connection_id>/<disconnect>': AdminAPI,
    'ws': FirstWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
