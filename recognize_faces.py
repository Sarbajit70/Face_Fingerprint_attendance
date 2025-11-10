import cv2
import face_recognition
import os
import datetime

known_faces = []
known_names = []

for filename in os.listdir('static/faces'):
    image = face_recognition.load_image_file(f'static/faces/{filename}')
    encoding = face_recognition.face_encodings(image)[0]
    known_faces.append(encoding)
    known_names.append(filename.split('.')[0])

camera = cv2.VideoCapture(0)
ret, frame = camera.read()
if ret:
    unknown_encoding = face_recognition.face_encodings(frame)[0]
    results = face_recognition.compare_faces(known_faces, unknown_encoding)
    if True in results:
        name = known_names[results.index(True)]
        print(f"Attendance marked for {name} at {datetime.datetime.now()}")
camera.release()