from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.response import Response


def hello_world(request):
    return Response()


if __name__ == '__main__':
    with Configurator(debug_logger=False) as config:
        config.add_route('hello', '/')
        config.add_view(hello_world, route_name='hello')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8000, app)
    server.serve_forever()
