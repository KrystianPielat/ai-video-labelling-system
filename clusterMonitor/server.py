from flask import Flask, request
from db_logger import logger

server = Flask(__name__)


@server.route("/log", methods=["POST"])
def log():
    print(request.get_data())
    return "OK", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=80, debug=True)
