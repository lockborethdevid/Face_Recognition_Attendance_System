import numpy as np
import face_recognition
import json
import pika
import os
import time
from datetime import datetime
import csv

def get_connection_amqp():
    credentials = pika.PlainCredentials("face-recognition", "face123")
    parameters = pika.ConnectionParameters(host="192.168.0.47",
                                           port=5672,
                                           credentials= credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    return channel

def getAttendance(student_info):
    channel.queue_declare("id_time_queue_8A", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="id_time_queue_8A",
        body = json.dumps(student_info),
        properties=pika.BasicProperties(
            delivery_mode=2, #make message persistent
        )
    )

def getDataset():
    with open("Batch_8A_Dataset_Test_MTCNN.csv") as f:
        reader = csv.reader(f)
        data = list(reader)
    # print(data)
    global student_list_encode
    global student_list_id
    global student_list_name
    student_list_encode = []
    student_list_id = []
    student_list_name = []
    for i in data:
        nested_data = i[1][1:len(i[1])-1]
        nested_data = nested_data.split()
        Face_encode = np.asarray(nested_data, dtype=np.float)
        Face_encode_Array = np.array(Face_encode)
        student_list_encode.append(Face_encode_Array)
        student_list_name.append(i[2])
        student_list_id.append(i[0])

def callback(ch, method, properties, body):
    try:
        #Load data from rabbitmq
        recieveData = json.loads(body)
        numpyArray = np.array(recieveData)
        convertString = numpyArray.tobytes()
        face_encode = np.frombuffer(numpyArray, dtype=float)
        #Compare encode face with dataset
        matches = face_recognition.compare_faces(student_list_encode, face_encode, tolerance=0.42)
        face_dis = face_recognition.face_distance(student_list_encode, face_encode)
        print(min(face_dis))
        matchIndex = np.argmin(face_dis)
        if matches[matchIndex]:
            id = student_list_id[matchIndex]
            name = student_list_name[matchIndex]
            current_date = str(datetime.now())
            print(name, id)
            getAttendance([id, current_date])
        else:
            print("no face matching")
    except Exception as e:
        print(e)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    getDataset()
    channel = get_connection_amqp()
    channel.queue_declare(queue="Devid_Queue_Test", durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="Devid_Queue_Test", on_message_callback=callback)
    channel.start_consuming()


