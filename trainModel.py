import cv2
import os
import numpy as np
import pickle

dataset_path = "dataset"

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
recognizer = cv2.face.LBPHFaceRecognizer_create()

known_encodings = []
labels = []

name_to_label = {}
current_label = 0

if not os.path.exists(dataset_path):
    print(f"Dataset path {dataset_path} not found.")
    exit(1)

for person_name in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person_name)
    if os.path.isdir(person_folder):
        if person_name not in name_to_label:
            name_to_label[person_name] = current_label
            current_label += 1
        
        for image_name in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_name)
            gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                continue
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            for (x, y, w, h) in faces:
                roi = gray[y:y+h, x:x+w]
                roi_resized = cv2.resize(roi, (100, 100))
                known_encodings.append(roi_resized)
                labels.append(name_to_label[person_name])

recognizer.train(known_encodings, np.array(labels))
recognizer.save("face_recognizer.yml")

with open("labels.pickle", "wb") as f:
    pickle.dump(name_to_label, f)

print("Modèle de reconnaissance faciale et labels sauvegardés.")
