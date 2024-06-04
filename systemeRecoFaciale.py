import cv2
import pickle
import numpy as np
import requests
import os
import time
from datetime import datetime
from threading import Thread

last_notification_time = 0
delay = 60  # Délai entre les notifications pour les visages inconnus
last_db_update_time_known = 0
last_db_update_time_unknown = 0

def send_pushbullet_notification(title, body, file_path):
    global last_notification_time
    current_time = time.time()
    if current_time - last_notification_time < delay:
        return
    last_notification_time = current_time

    def send_request():
        access_token = "o.ewd1uhLYy2kTk6xMOejUBGXqxnDxi6po"
        headers = {"Access-Token": access_token}
        try:
            with open(file_path, 'rb') as file:
                files = {'file': file}
                resp = requests.post("https://api.pushbullet.com/v2/upload-request", json={"file_name": os.path.basename(file_path), "file_type": "image/jpeg"}, headers=headers)
                if resp.status_code != 200:
                    print("Failed to get upload URL")
                    return
                upload_data = resp.json()

                upload_resp = requests.post(upload_data['upload_url'], files=files)
                if upload_resp.status_code != 204:
                    print("Failed to upload image")
                    return

                push_data = {
                    "type": "file", 
                    "file_name": os.path.basename(file_path), 
                    "file_type": "image/jpeg", 
                    "file_url": upload_data["file_url"], 
                    "body": body, 
                    "title": title
                }
                response = requests.post("https://api.pushbullet.com/v2/pushes", headers=headers, json=push_data)
                if response.status_code == 200:
                    print("Notification sent.")
                else:
                    print("Failed to send notification.")
        except Exception as e:
            print(f"Error sending notification: {e}")
    if file_path:  # Only start thread if file_path is not None
        Thread(target=send_request).start()
   


def upload_to_database(file_path, person_name):
    global last_db_update_time_known, last_db_update_time_unknown
    current_time = time.time()
    
    if person_name == "Inconnu":
        if current_time - last_db_update_time_unknown < delay:
            return
        last_db_update_time_unknown = current_time
    else:
        if current_time - last_db_update_time_known < delay:
            return
        last_db_update_time_known = current_time

    url = 'http://localhost/face_recognition/upload.php' 
    capture_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    files = {'image': open(file_path, 'rb')}
    data = {
        'capture_time': capture_time,
        'person_name': person_name  # Ajout du nom de la personne
    }
    
    response = requests.post(url, files=files, data=data)
    print(response.text)

def open_door():
    print("Door opened!")

# Load the face cascade and the face recognizer model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('face_recognizer.yml')

# Load the label names
with open('labels.pickle', 'rb') as f:
    labels = pickle.load(f)
    labels = {v: k for k, v in labels.items()}

# Directory to save captures
capture_dir = "captures"
if not os.path.exists(capture_dir):
    os.makedirs(capture_dir)

# Start video capture
print("[INFO] starting video stream...")
cap = cv2.VideoCapture(0)

last_unknown_save_time = 0
unknown_save_interval = 60  # seconds

stop_time = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        id_, confidence = recognizer.predict(roi_gray)

        if confidence < 80:  
            if not stop_time:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                print(f"Recognized {labels[id_]} with confidence: {confidence}")
                person_name = labels[id_]
                open_door()
                # Save recognized face capture
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                stop_time = time.time() + 15 
                file_path = os.path.join(capture_dir, f"{person_name}_{timestamp}.jpg")
                cv2.imwrite(file_path, frame)
                upload_to_database(file_path,person_name)
        else:
            current_time = time.time()
            if current_time - last_unknown_save_time > unknown_save_interval:
                print(f"Unknown face detected with confidence: {confidence}")
                person_name = "Inconnu"
                # Save unknown face capture
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                file_path = os.path.join(capture_dir, f"{person_name}_{timestamp}.jpg")
                cv2.imwrite(file_path, frame)
                last_unknown_save_time = current_time
                #send_pushbullet_notification("ATTENTION", "Un visage inconnu est détecté à la porte.", file_path)
                upload_to_database(file_path,person_name)

        
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, person_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    cv2.imshow("Face Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q') or (stop_time and time.time() > stop_time):
        break

cap.release()
cv2.destroyAllWindows()
