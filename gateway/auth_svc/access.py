import os, requests
from logger import log


def login(request):
    auth = request.authorization
    if not auth:
        log("info", "Missing credentials in user request")
        return None, ("Missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login", auth=basicAuth
    )

    if response.status_code != 200:
        log("info", "Error from auth service: {}".format(response.text))
        return None, (response.text, response.status_code)

    return response.text, None


def token(request):
    if "Authorization" not in request.headers:
        log("info", "Missing credentials in user request")
        return None, ("Missing credentials", 401)

    token = request.headers["Authorization"]

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token},
    )

    if response.status_code != 200:
        log("info", "Error response code from validate request to auth service")
        return None, (response.text, response.status_code)

    return response.text, None
