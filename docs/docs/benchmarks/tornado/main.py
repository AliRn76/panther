from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler


class MainHandler(RequestHandler):
    def get(self):
        self.write({})


def make_app():
    return Application([
        (r'/', MainHandler),
    ])


if __name__ == '__main__':
    app = make_app()
    server = HTTPServer(app)
    server.bind(8000)
    server.start(1)
    IOLoop.current().start()
