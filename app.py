from flask import Flask, render_template, request, redirect, url_for, flash
import cv2
import os
import face_recognition
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'
FACE_FOLDER = 'static/faces'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    c.execute('''SELECT attendance.timestamp, users.name 
                 FROM attendance JOIN users ON attendance.user_id = users.id
                 ORDER BY attendance.timestamp DESC''')
    records = c.fetchall()
    conn.close()
    return render_template('index.html', users=users, records=records)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        # Capture image from webcam
        camera = cv2.VideoCapture(0)
        ret, frame = camera.read()
        if ret:
            filename = f"{name}_{int(datetime.now().timestamp())}.jpg"
            filepath = os.path.join(FACE_FOLDER, filename)
            cv2.imwrite(filepath, frame)
            # Save to database
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO users (name, image) VALUES (?, ?)', (name, filename))
            conn.commit()
            conn.close()
            flash(f"User {name} registered successfully!", "success")
        else:
            flash("Failed to capture image.", "danger")
        camera.release()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/attendance', methods=['POST'])
def attendance():
    # Load known faces
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, name, image FROM users')
    users = c.fetchall()
    known_encodings = []
    user_ids = []
    for user in users:
        image_path = os.path.join(FACE_FOLDER, user[2])
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_encodings.append(encodings[0])
            user_ids.append(user[0])

    # Capture image from webcam
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    if ret:
        unknown_encodings = face_recognition.face_encodings(frame)
        if unknown_encodings:
            results = face_recognition.compare_faces(known_encodings, unknown_encodings[0])
            if True in results:
                idx = results.index(True)
                user_id = user_ids[idx]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute('INSERT INTO attendance (user_id, timestamp) VALUES (?, ?)', (user_id, timestamp))
                conn.commit()
                flash(f"Attendance marked for {users[idx][1]} at {timestamp}", "success")
            else:
                flash("Face not recognized.", "warning")
        else:
            flash("No face detected in the frame.", "danger")
    else:
        flash("Failed to capture image.", "danger")
    camera.release()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(FACE_FOLDER):
        os.makedirs(FACE_FOLDER)
    init_db()
    app.run(debug=True)