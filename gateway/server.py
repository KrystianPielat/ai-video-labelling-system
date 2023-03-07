from flask import Flask, request
from auth_svc import access
import requests

server = Flask(__name__)


def log(level, log):
    requests.post(
        "http://monitor:8080/log",
        data={"source": "gateway", "log": log, "level": level},
    )


@server.route("/")
def home():
    return "Hi", 200


@server.route("/login", methods=["POST"])
def login_endpoint():
    token, err = access.login(request)

    if not err:
        return token
    log("error", "Login error: " + str(err))
    return err


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
