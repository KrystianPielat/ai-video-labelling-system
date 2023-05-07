from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import schemas
import uvicorn
from datetime import datetime
import os
import pika
import json

app = FastAPI()


@app.get("/get_messages/{queue}", response_model=schemas.ContainerList)
def get_containers(queue: str):

    return JSONResponse(status_code=404, content={"message": "Something went wrong"})


@app.get("/filter/{queue}")
def filter_rabit(queue, request: Request, ack=False):

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        channel = connection.channel()
        matches = []

        while True:
            method_frame, header_frame, body = channel.basic_get(queue=queue)
            if not body:
                break

            message = json.loads(body)

            if request.query_params:
                for k, v in dict(request.query_params).items():
                    if message.get(k) != v:
                        continue

            matches.append(message)

            if ack:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        connection.close()
    except Exception as err:
        return JSONResponse(status_code=500, content={"error": str(err)})
    return matches


@app.get("/filter2/{queue}")
def filter_rabbit2(queue, request: Request, ack=False):
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    bodies = []

    def callback(ch, method, properties, body):
        bodies.append("[x] Received %r" % body)

    channel.basic_consume(queue=queue, on_message_callback=callback)
    channel.start_consuming()
    connection.close()

    return bodies 


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True, workers=3)
