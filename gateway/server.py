import json
import requests
import gridfs
import pika
from bson.objectid import ObjectId
from flask import Flask, render_template, request, send_file, session, redirect, url_for
from flask_pymongo import PyMongo
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from auth_svc import access
from logger import log
from storage import util
import io


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


server = Flask(__name__)
server.secret_key = "sarcasm"

mongo_unlabeled = PyMongo(server, uri="mongodb://mongodb:27017/unlabeled")

mongo_labeled = PyMongo(server, uri="mongodb://mongodb:27017/labeled")

fs_unlabeled = gridfs.GridFS(mongo_unlabeled.db)
fs_labeled = gridfs.GridFS(mongo_labeled.db)


def require_api_token(func):
    def check_token(*args, **kwargs):

        if not access.verify(request, session):
            return "Not authorized", 403
        return func(*args, **kwargs)

    return check_token


@server.route("/debug")
def debug():
    unlabeled = util.filter_rabit(
        "unlabeled", username=access.decode(request, session)[0]["username"]
    )
    log("debug", "deb" + unlabeled[0]["username"])
    return "OK", 200


@server.route("/", methods=["GET", "POST"])
def home():
    # Set session token on login
    if request.method == "POST":
        token, err = access.login(request)
        if err:
            return err
        session["auth_token"] = "Bearer " + token

    # Display page
    if access.verify(request, session):
        labeled = util.filter_rabit(
            "labeled", username=access.decode(request, session)[0]["username"]
        )
        unlabeled = util.filter_rabit(
            "unlabeled", username=access.decode(request, session)[0]["username"]
        )
        return render_template("home.html", labeled=labeled, unlabeled=unlabeled)
    return render_template("login.html", form=LoginForm())


@server.route("/upload", methods=["POST"])
def upload():

    data, err = access.decode(request, session)

    if err:
        return err

    if data["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            fid = util.upload(f, fs_unlabeled)
            if not fid:
                log("error", "Error uploading file to mongo")
                break

            message = {
                "unlabeled_fid": str(fid),
                "labeled_fid": None,
                "username": data["username"],
                "filename": f.filename,
            }
            if not util.rabbit_publish("unlabeled", message):
                fs_unlabeled.delete(fid)
                log("Failed publishing rabbitmq message")
                break

        return redirect(url_for("home"))
    return "not authorized", 401


@server.route("/download", methods=["GET"])
def download():
    data, err = access.decode(request, session)

    if err:
        return err

    if data["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            obj_id = ObjectId(fid_string)
            out_bytes = fs_labeled.get(obj_id).read()
            util.delete(obj_id, fs_labeled)

            util.filter_rabit("labeled", ack=True, labeled_fid=fid_string)
            return send_file(
                io.BytesIO(out_bytes), download_name=f"{fid_string}.mp4", as_attachment=True
            )
        except Exception as err:
            log("error", "Error pulling labeled video from mongo: " + str(err))
            return "internal server error", 500

    return "not authorized", 401


@server.route("/nogui/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if err:
        return err

    return token


@server.route("/nogui/upload", methods=["POST"])
def upload_nogui():

    data, err = access.decode(request, session)

    if err:
        return err

    if data["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            fid = util.upload(f, fs_unlabeled)
            if not fid:
                log("error", "Error uploading file to mongo")
                break

            message = {
                "unlabeled_fid": str(fid),
                "labeled_fid": None,
                "username": data["username"],
                "filename": f.filename,
            }
            if not util.rabbit_publish("unlabeled", message):
                fs_unlabeled.delete(fid)
                log("Failed publishing rabbitmq message")
                break

        return "success!", 200
    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
