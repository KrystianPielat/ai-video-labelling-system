from flask import Flask, request, render_template
from logs import logger
import logging

server = Flask(__name__)
log = logging.getLogger("werkzeug")
log.disabled = True

# Not rly used
@server.route("/", methods=["GET"])
def logs_list():
    with open("cluster_logs", "r") as f:
        data = f.read().splitlines()
    return render_template("logs.html", logs_list=data)


@server.route("/log", methods=["POST"])
def log():
    logger.log(
        request.form.get("level"),
        request.form.get("source"),
        request.form.get("log"),
        request.form.get("filename"),
        request.form.get("line"),
    )
    return "OK", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=False)
