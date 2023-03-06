from flask import Flask, request
import requests, os

server = Flask(__name__)


def login(request):
    auth = request.authorization
    if not auth:
        return None, ("Missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login", auth=basicAuth
    )

    if response.status_code == 200:
        return response.text, None
    return None, (response.text, response.status_code)


@server.route("/")
def home():
    return "Hi", 200


@server.route("/login", methods=["POST"])
def login_endpoint():
    token, err = login(request)

    if not err:
        return token
    return err


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
