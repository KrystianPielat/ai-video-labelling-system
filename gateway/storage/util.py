import pika, json
from logger import log


def upload(f, fs, channel, access):
    pass
    try:
        fid = fs.put(f)
    except Exception as err:
        log(
            "error",
            "Internal server error when uploading unlabeled video to mongo: " + str(err),
            True,
        )
        return "internal server error", 500

    message = {
        "unlabeled_fid": str(fid),
        "labeled_fid": None,
        "username": access["username"],
    }

    try:
        # connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        # channel = connection.channel()
        channel.basic_publish(
            exchange="",
            routing_key="unlabeled",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        log(
            "error",
            "Internal server error when posting upload message"
            + "to unlabeled queue: "
            + str(err),
            True,
        )
        fs.delete(fid)
        return "internal server error", 500
