import csv
import face_recognition
from facenet_pytorch import MTCNN
import cv2
from PIL import Image
import numpy as np
import os
import sys


# def mtcnn_detect(directory, pictures):
#     list_dir = os.listdir(directory)
#     # Create single face detector
#     mtcnn = MTCNN(margin=20, select_largest=False, post_process=False)
#     for pic in list_dir:
#         if pic.endswith(".jpg") or pic.endswith(".png"):
#             frame = cv2.imread(f'{directory}/{pic}')
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             mtcnn_frame = Image.fromarray(frame)
#             face = mtcnn(mtcnn_frame)
#             face_img = face.permute(1, 2, 0).int().numpy()
#             print("Done permute face")
#             os.chdir(pictures)
#             cv2.imwrite(f"{pic}", face_img)


def createDataset(path):
    os.chdir(sys.path[0])
    with open("Batch_8A_Dataset_Test_MTCNN.csv", mode="a", newline='') as dataset:
        datasetWriter = csv.writer(dataset, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        list_dir = os.listdir(path)
        for pic in list_dir:
            if pic.endswith(".jpg") or pic.endswith(".png"):
                img = face_recognition.load_image_file(f'{path}/{pic}')
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                face_location = face_recognition.face_locations(rgb_img)
                face_encode = face_recognition.face_encodings(rgb_img, face_location)[0]
                print(pic)
                id, name = os.path.splitext(pic)[0].split("_")
                print(name, id)
                datasetWriter.writerow([id, face_encode, name])

directory = sys.path[0] + "/Face_Pictures"
# save_dir = sys.path[0] + "/Face_Pictures"

# mtcnn_detect(directory, save_dir)
createDataset(directory)
