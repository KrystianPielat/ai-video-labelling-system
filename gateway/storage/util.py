import pika, json
from logger import log
import requests


def delete(f, fs):
    try:
        fs.delete(f)
    except Exception as err:
        log(
            "error",
            "Internal server error when deleting video from mongo: " + str(err),
            True,
        )
        return False
    return True 


def rabbit_publish(queue, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    try:
        channel.basic_publish(
            exchange="",
            routing_key="unlabeled",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as ex:
        log("error", "Failed publishing rabbit msq:" + str(ex))
        return False
    return True


def upload(f, fs):
    try:
        fid = fs.put(f)
    except Exception as err:
        log(
            "error",
            "Internal server error when uploading unlabeled video to mongo: "
            + str(err),
            True,
        )
        return None

    return fid


def filter_rabit(queue, ack=False, **kwargs):

    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    matches = []
    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue)
        if not body:
            break
        for k, v in kwargs.items():
            message = json.loads(body)
            if message.get(k) == v:
                if ack:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                matches.append(message)

    connection.close()

    return matches
