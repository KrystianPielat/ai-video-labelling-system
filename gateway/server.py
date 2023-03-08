from flask import Flask, request
from auth_svc import access
from logger import log
import json
import pika
from storage import util
from flask_pymongo import PyMongo
import gridfs

server = Flask(__name__)

mongo_unlabeled = PyMongo(
    server, uri="mongodb://mongodb:27017/unlabeled"
)

mongo_labeled = PyMongo(server, uri="mongodb://mongodb:27017/labeled")

fs_unlabeled = gridfs.GridFS(mongo_unlabeled.db)
fs_labeled = gridfs.GridFS(mongo_labeled.db)


@server.route("/")
def home():
    return "Hi", 200


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if err:
        return err

    return token


@server.route("/upload", methods=["POST"])
def upload():

    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    access_data, err = access.token(request)

    if err:
        return err

    access_data = json.loads(access_data)

    if access_data["admin"]:
        if len(request.files) != 1:
            log("info", "User tried to send too many files")
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = util.upload(f, fs_unlabeled, channel, access_data)
            if err:
                return err

        return "success!", 200
    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
