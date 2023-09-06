import json

import uvloop
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.log import access_log
from tornado.web import Application, url, RequestHandler


# Fake API
class FakeAPI(RequestHandler):

    async def get(self, *args, **kwargs):
        self.set_status(202)
        return self.write(chunk={'detail': 'Ok'})


# Main API
class MainAPI(RequestHandler):

    async def put(self, user, record):
        """
        1. Check Method
        2. Check Authorization Header
        3. Read Body
        4. Read Query Params
        5. Read Path Variables
        6. Return Json Response
        """

        if not self.request.headers.get('authorization'):
            self.set_status(401)
            return self.write(chunk={'detail': 'Authorization Error'})

        query = {k: v[0].decode() for k, v in self.request.arguments.items()}
        data = {
            'params': {
                'user': int(user),
                'record': int(record),
            },
            'query': query,
            'data': json.loads(self.request.body or '{}'),
        }
        self.set_status(200)
        return self.write(chunk=data)


# Routing
for n in range(50):
    pre_fake_url_routing = [url(f'users/(.*)/{n}', FakeAPI)]
    post_fake_url_routing = [url(f'fake-route-{n}/(.*)', FakeAPI)]

main_url_routing = [url('/users/([^/]+)/records/(.+)', MainAPI)]
app = Application(pre_fake_url_routing + main_url_routing + post_fake_url_routing)


# Project Config
if __name__ == '__main__':
    uvloop.install()
    server = HTTPServer(app)
    server.bind(8000, reuse_port=True)
    server.start()
    access_log.setLevel('ERROR')
    IOLoop.current().start()
