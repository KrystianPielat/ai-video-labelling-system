from flask import Flask


server = Flask(__name__)


@server.route("/")
def home():
    return "Hi", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
