import cherrypy


class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        return


if __name__ == '__main__':
    cherrypy.config.update({
        'environment': 'production',
        'server.socket_port': 8000,
        'log.screen': False,
    })
    cherrypy.quickstart(HelloWorld())
