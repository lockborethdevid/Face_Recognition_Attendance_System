import pika
import json
import queue

my_queue = queue.Queue()

def get_q_fun():
    credentail = pika.PlainCredentials('face-recognition', 'face123')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='192.168.0.47', port=5672, credentials=credentail))
    channel = connection.channel()
    channel.queue_declare(queue='id_time_vid', durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        my_queue.put(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='id_time_vid', on_message_callback=callback)
    channel.start_consuming()
