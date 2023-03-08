import requests
import inspect


def get_linenumber():
    cf = inspect.currentframe()
    return cf.f_back.f_lineno


def get_filename():
    return inspect.stack()[1].filename


def log(level, log, loc=False):
    data = {
        "source": "converter",
        "log": log,
        "level": level,
    }
    if loc:
        data["filename"] = get_filename()
        data["line"] = get_linenumber()
    requests.post(
        "http://monitor:8080/log",
        data=data,
    )
