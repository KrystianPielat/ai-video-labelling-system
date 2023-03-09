import os, requests, json
from logger import log


def login(request):
    creds = (
        (request.authorization.username, request.authorization.password)
        if request.authorization
        else (request.form.get("username"), request.form.get("password"))
    )
    if not creds:
        return None, ("Missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
        auth=creds,
    )

    if response.status_code != 200:
        return None, (response.text, response.status_code)

    return response.text, None


def decode(request, session=None):
    if session and session.get("auth_token"):
        headers = {"Authorization": session.get("auth_token")}
    elif "Authorization" in request.headers:
        headers = request.headers
    else:
        return None, ("Missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/decode",
        headers=headers,
    )

    if response.status_code != 200:
        return None, (response.text, response.status_code)

    return json.loads(response.text), None


def verify(request, session=None):
    if session and session.get("auth_token"):
        headers = {"Authorization": session.get("auth_token")}
    else:
        headers = request.headers
    if (
        requests.post(
            f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/verify", headers=headers
        ).status_code
        != 200
    ):
        return False
    return True
