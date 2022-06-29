import face_recognition, cv2, threading, time, datetime, os, sys
from multiprocessing import Process, Manager, cpu_count, Queue
from video_capture import videoCapture
from PIL import Image
from facenet_pytorch import MTCNN
from detection import detect
from q2rabbitmq import from_q_to_rabbitmq
from prev_next_id import prev_id, next_id

# A subprocess use to capture frames
def capture(read_frame_list, Global, worker_num):
    # video_capture = videoCapture("rtsp://admin:face$can@10.2.7.200")
    # video_capture = videoCapture("http://<IP>/video")
    video_capture = videoCapture(0)
    fps = 4
    startTime = time.time()
    while not Global.is_exit:
        # If it's time to read frame
        if Global.buff_num != next_id(Global.read_num, worker_num):
            # Grab a single frame from video
            frame = video_capture.read()
            nowTime = time.time()
            if int(nowTime - startTime) > fps:
                read_frame_list[Global.buff_num] = [frame, str(datetime.datetime.now())]
                Global.buff_num = next_id(Global.buff_num, worker_num)
                startTime = time.time()  # reset startTime to become nowTime
                # print(datetime.datetime.now())

# Many subprocess use to process frames
def process(worker_id, read_frame_list, Global, worker_num, put_get):
    while not Global.is_exit:
        # Wait to read frame
        while Global.read_num != worker_id or Global.read_num != prev_id(Global.buff_num, worker_num):
            # If user requested to end the app , then stop waiting for webcam
            if Global.is_exit:
                break
            time.sleep(0.01)
        try:
            # Read a single frame from frame list
            frame_process = read_frame_list[worker_id][0]
            # Expect next worker to read frame
            Global.read_num = next_id(Global.read_num, worker_num)
            # Convert image from BGR which OpenCV use to RGB color which face recognition use
            rgb_frame = frame_process[:, :, ::-1]
        #     # print("process")
        #     # Find all the faces and face encodings in the frame of video
        #     face_locations = face_recognition.face_locations(rgb_frame, model="cnn" )
        #     face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        #     # send encodes to q
        #     if len(face_encodings) != 0:
        #         # print("faces : " + str(len(face_encodings)))
        #         # for face_lo in face_locations:
        #         #     top, right, bottom, left = face_lo
        #         #     img = frame_process[top - 20: bottom + 20, left - 15: right + 15]
        #         #     plt.imshow(img)
        #             plt.show()
        #         put_get.put(face_encodings)
        #         print("Done put 1 face encode")
        # except:
        #     print("error while processing")


            # Convert frame to mtcnn frame which will use by facenet_pytorch
            mtcnn_frame = Image.fromarray(rgb_frame)
            # Declare both mtcnn function include single and multiple face detection
            mtcnn1 = MTCNN( margin=20, select_largest=False, post_process=False)
            mtcnn2 = MTCNN( margin=20, keep_all=True, post_process=False)
            # Declare and read directory which we will store cropped face image
            directory = sys.path[0] + "\Photos"
            detect_face = detect(mtcnn_frame, mtcnn1, mtcnn2, directory)

            # Find all the faces and face encodings in the frame of video
            # face_location = face_recognition.face_locations(rgb_frame,model="cnn")
            # face_encodings = face_recognition.face_encodings(rgb_frame,face_location)
        except:
            # print("Error While processing")
            pass
        for pic in os.listdir(directory):
            if pic.endswith(".png") or pic.endswith(".jpg"):
                try:
                    img = face_recognition.load_image_file(f'{directory}/{pic}')
                    rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_location = face_recognition.face_locations(rgb_frame, model="cnn")
                    face_encode = face_recognition.face_encodings(rgb_frame,face_location, num_jitters=10)[0]
                    print("Done encode " + pic)
                    if (len(face_encode)) != 0:
                        put_get.put(face_encode)
                        print(f"Done put face encode {pic} to queue")
                        try:
                            os.remove(directory + "/" + pic)
                            print("Done remove " + pic)
                        except FileNotFoundError:
                            pass
                except:
                    print("Can't encode " + pic)
                    try:
                        os.remove(directory + "/" + pic)
                        print("Done remove" + pic)
                    except FileNotFoundError:
                        pass


if __name__ == "__main__" :
    Global = Manager().Namespace()
    Global.read_num = 1
    Global.buff_num = 1
    Global.is_exit = False
    read_frame_list = Manager().dict()
    put_get = Queue()

    # Number of workers (subprocess use to process frames)
    if cpu_count() > 2:
        worker_num = cpu_count() - 2
    else:
        worker_num = 2

    # Subprocess list
    p1 = list()
    # Create thread to capture frames
    p1.append(threading.Thread(target=capture, args=(read_frame_list, Global, worker_num,)))
    p1[0].start()

    # Create workers
    for worker_id in range(1, worker_num + 1):
        p1.append(
            Process(target=process, args=(worker_id, read_frame_list, Global, worker_num, put_get))
        )
        p1[worker_id].start()

    q2 = threading.Thread(target=from_q_to_rabbitmq, args=(put_get,))
    q2.start()
