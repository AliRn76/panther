from flask import Flask, Response

app = Flask(__name__)


@app.route("/")
def hello_world():
    return Response(status=200)
