from flask import Flask, request
from auth_svc import access
import requests

server = Flask(__name__)


@server.route("/")
def home():
    requests.post(
        "http://monitor/log",
        data={
            "source": "gateway",
            "log": "logggg",
        },
    )
    return "Hi", 200


@server.route("/login", methods=["POST"])
def login_endpoint():
    token, err = access.login(request)

    if not err:
        return token
    return err


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=80, debug=True)
