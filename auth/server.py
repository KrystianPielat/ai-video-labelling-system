from flask import Flask, request
import jwt, datetime, os
import psycopg2


server = Flask(__name__)


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return "Missing credentials", 401

    conn = psycopg2.connect(
        host=os.environ.get("PSQL_HOST"),
        database=os.environ.get("PSQL_DB"),
        user=os.environ.get("PSQL_USER"),
        password=os.environ.get("PSQL_PASSWORD"),
        port="5432",
    )

    cur = conn.cursor()

    cur.execute("SELECT email, password FROM users WHERE email=%s", (auth.username,))
    try:
        user_row = cur.fetchone()
        if not user_row:
            return "Invalid credentials", 401
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "Invalid credentials", 401
        return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    except Exception as ex:
        print(ex)
    return "Invalid credentials", 401


@server.route("/decode", methods=["POST"])
def decode():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "Missing credentials", 401

    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )

        return decoded, 200
    except Exception as ex:
        print(ex)
    return "Not authorized", 403


@server.route("/verify", methods=["POST"])
def verify():
    encoded_jwt = request.headers["Authorization"] or request.args.get("token")

    if not encoded_jwt:
        return "Missing credentials", 401

    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        jwt.decode(encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"])

        return "Authorized", 200
    except Exception as ex:
        print(ex)
    return "Not authorized", 403


def createJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
