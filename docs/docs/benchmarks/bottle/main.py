from bottle import Bottle, HTTPResponse

app = Bottle()


@app.route('/')
def index(*args, **kwargs):
    return HTTPResponse(status=200)

