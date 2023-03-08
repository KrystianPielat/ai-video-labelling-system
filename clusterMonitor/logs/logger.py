import requests, logging


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[1;36m"
    reset = "\x1b[0m"
    format = "%(asctime)s | [%(levelname)s] | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logging.basicConfig(filename="cluster_logs", filemode="a")

logger = logging.getLogger("clusterMonitor")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)


def log(level, source, msg, filename=None, line=None):
    if filename and line:
        msg = (
            f"{CustomFormatter.blue}[{source}][{filename}:{line}]"
            + f"{CustomFormatter.reset}:  {msg}"
        )
    else:
        msg = f"{CustomFormatter.blue}[{source}]{CustomFormatter.reset}:  {msg}"
    return getattr(logger, level.lower())(msg)
