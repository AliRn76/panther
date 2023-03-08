from bottle import route, run, HTTPResponse


@route('/')
def index(*args, **kwargs):
    return HTTPResponse(status=200)


run(host='localhost', port=8000, quiet=True)
