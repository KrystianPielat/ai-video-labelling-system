from flask import Flask, request
from logs import logger
import logging

server = Flask(__name__)
log = logging.getLogger("werkzeug")
log.disabled = True


@server.route("/log", methods=["POST"])
def log_endpoint():
    logger.log(
        request.form.get("level"), request.form.get("source"), request.form.get("log")
    )
    return "OK", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=False)
