import pika
import json


# function to get connection with rabbitmq
def get_connection_amqp():
    credentials = pika.PlainCredentials("face-recognition", "face123")
    parameters = pika.ConnectionParameters(host="192.168.0.47",
                                           port=5672,
                                           credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue="Devid_Queue_Test", durable=True)
    return channel


# function to send encode data to queue in rabbitmq
def publish_data(encoding, channel):
    res = encoding.tolist()
    channel.basic_publish(
        exchange="",
        routing_key='Devid_Queue_Test',
        body=json.dumps(res),
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )
