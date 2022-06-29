import pika
import json
def getQueueConnection():
    credentail = pika.PlainCredentials('face-recognition', 'face123')
    connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='192.168.0.47', port=5672, virtual_host='/', credentials=credentail))
    global channel
    channel = connection.channel()
    return channel

def getAttendance(student_info, channel):
    channel.queue_declare(queue ='id_time_vid', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='id_time_vid',
        body=json.dumps(student_info),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
if __name__=="__main__":
    channel = getQueueConnection()
    test_list = [[31, "2021-08-03 15:04:20.369652"], [8, "2021-08-03 15:04:20.369652"]]
    for i in test_list:
        for j in range(0, 7):
            getAttendance(i, channel)
    print("Done push")
