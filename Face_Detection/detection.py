import cv2
import os
from matplotlib import pyplot as plt
import face_recognition
import random


# Detect and crop single face in an image
def single_face(mtcnn1, mtcnn_frame):
    face = mtcnn1(mtcnn_frame)
    img = face.permute(1, 2, 0).int().numpy()
    return img


# Detect and crop multiple faces in an image
def multiple_faces(mtcnn2, mtcnn_frame):
    all_img = []
    faces = mtcnn2(mtcnn_frame)
    fig, axes = plt.subplots(1, len(faces))
    for face, ax in zip(faces, axes):
        img = face.permute(1, 2, 0).int().numpy()
        all_img.append(img)
    return all_img


# Save cropped face as image and store in a directory
def save(directory, img):
    os.chdir(directory)
    i = random.randint(1, 10000)
    cv2.imwrite("img" + str(i) + ".png", img)


# Detect both single or multiple face in an image
def detect(mtcnn_frame, mtcnn1, mtcnn2, directory):
    try:
        try:
            all_img = multiple_faces(mtcnn2, mtcnn_frame)
            for img in all_img:
                save(directory, img)
        except:
            img = single_face(mtcnn1, mtcnn_frame)
            save(directory, img)
    except:
        pass
    return detect_face
