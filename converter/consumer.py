import numpy as np
import cv2
import subprocess
import os
import sys
import tempfile
from bson.objectid import ObjectId
import pika
from pymongo import MongoClient
import gridfs
from logger import log
import json

prototxt_path = "./models/MobileNetSSD_deploy.prototxt.txt"
model_path = "./models/MobileNetSSD_deploy.caffemodel"
min_confidence = 0.3

classes = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]

np.random.seed(24214)

colors = np.random.uniform(0, 255, size=(len(classes), 3))

net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)


def label_img(image):
    height, width = image.shape[0], image.shape[1]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007, (300, 300), 130)
    net.setInput(blob)
    detected_objects = net.forward()
    for i in range(detected_objects.shape[2]):
        confidence = detected_objects[0][0][i][2]

        if confidence > min_confidence:
            class_index = int(detected_objects[0, 0, i, 1])
            upper_left_x = int(detected_objects[0, 0, i, 3] * width)
            upper_left_y = int(detected_objects[0, 0, i, 4] * height)
            lower_right_x = int(detected_objects[0, 0, i, 5] * width)
            lower_right_y = int(detected_objects[0, 0, i, 6] * height)

            prediction_text = f"{classes[class_index]}: {int(confidence*100)}%"

            cv2.rectangle(
                image,
                (upper_left_x, upper_left_y),
                (lower_right_x, lower_right_y),
                colors[class_index],
            )

            cv2.putText(
                image,
                prediction_text,
                (
                    upper_left_x,
                    upper_left_y - 15 if upper_left_y > 30 else upper_left_y + 15,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                colors[class_index],
                2,
            )

    return image


def label_video(file):
    tmp = tempfile.NamedTemporaryFile(dir="./tmp", suffix=".mp4")

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            file.name,
            "-qscale",
            "0",
            "-y",
            tmp.name,
            "-loglevel",
            "quiet",
        ]
    )

    cap = cv2.VideoCapture(tmp.name)

    # Video height and width
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    print(f"Height {height}, Width {width}")

    # Get FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"FPS : {fps:0.2f}")
    cap.release()

    VIDEO_CODEC = "mp4v"
    tmp_write = tempfile.NamedTemporaryFile(dir="./tmp", suffix=".mp4")
    out = cv2.VideoWriter(
        tmp_write.name,
        cv2.VideoWriter_fourcc(*VIDEO_CODEC),
        fps,
        (int(width), int(height)),
    )

    cap = cv2.VideoCapture(tmp.name)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for frame in range(n_frames):
        ret, img = cap.read()
        if ret is False:
            break
        img = label_img(img)
        out.write(img)

    out.release()
    cap.release()
    tmp.close()

    result_file = tempfile.NamedTemporaryFile(dir="./tmp", suffix=".mp4")

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            tmp_write.name,
            "-crf",
            "18",
            "-preset",
            "veryfast",
            "-vcodec",
            "libx264",
            "-y",
            result_file.name,
            "-loglevel",
            "quiet",
        ]
    )

    tmp_write.close()

    return result_file


def convert(message, fs_unlabeled, fs_labeled, channel):
    try:
        tf = tempfile.NamedTemporaryFile(dir="./tmp", suffix=".mp4")
        unlabeled_vid_id = ObjectId(message["unlabeled_fid"])
        out = fs_unlabeled.get(unlabeled_vid_id)
        tf.write(out.read())

        output_file = label_video(tf)

        fid = fs_labeled.put(output_file)

        output_file.close()
        tf.close()

        fs_unlabeled.delete(unlabeled_vid_id)

    except Exception as err:
        log(
            "error",
            "Error labelling a video with fid:" + {message["unlabeled_fid"]},
            True,
        )
        return err

    try:
        message["labeled_fid"] = str(fid)
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("LABELED_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        fs_labeled.delete(fid)
        log("error", "Failed to publish labeled_vid message", True)
        return err

    return None


def main():

    client = MongoClient("mongodb", 27017)

    db_unlabeled = client.unlabeled
    db_labeled = client.labeled

    fs_unlabeled = gridfs.GridFS(db_unlabeled)
    fs_labeled = gridfs.GridFS(db_labeled)

    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        message = json.loads(body)
        err = convert(message, fs_unlabeled, fs_labeled, channel)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            log("info", "Successfully labelled video for user " + message["username"])
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("UNLABELED_QUEUE"), on_message_callback=callback
    )

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os.exit(0)
