import cv2
import face_recognition
import os

name = input("Enter your name: ")
camera = cv2.VideoCapture(0)
ret, frame = camera.read()
if ret:
    cv2.imwrite(f'static/faces/{name}.jpg', frame)
    print(f"Face registered for {name}")
camera.release()