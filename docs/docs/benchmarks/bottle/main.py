from bottle import Bottle, route, run, HTTPResponse

app = Bottle()


@app.route('/')
def index(*args, **kwargs):
    return HTTPResponse(status=200)

