import cv2
from flask import Flask, render_template, Response, request
import requests
from time import sleep
# from flask_googlemaps import GoogleMaps, Map

import random

def create_app():
    """Initialize the application"""
    app = Flask(__name__)
    
    #Defualt values used by the app
    app.config.from_mapping(SECRET_KEY = 'dev')
    
    #Add stuff here to ensure that the directory exists?
    
    # Set up path routing. Avoids 404.
    @app.route('/', methods=['POST', 'GET'])  # will we need post?
    def index():
        return render_template('index.html') # Handle get, just view page
    
    @app.route('/video_feed', methods=['POST', 'GET'])
    def video_feed():
        """Video streaming route. Put this in the src attribute of an img tag."""
        if request.method == 'POST':
            if request.form.get('submit') == 'Zoom In':
                print("Hello World")
                pass # do something
            else:
                pass # unknown
        
        return Response(gen_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
        
    return app


app = create_app()

# you can set key as config
# app.config['GOOGLEMAPS_KEY'] = "AIzaSyBeLoqOhI7Px_J2WUhkXlJ4cdxkl_hWk7Q"

# Initialize the extension
# GoogleMaps(app)

camera = cv2.VideoCapture(0)

def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # frame = zoom(frame, 2)
            #frame = box_faces(frame)
            response = requests.get("http://localhost:8080/bee/beeInfo")
            x1,y1,x2,y2,angle,lat,long = beeInfoParser(response)
            frame = cv2.rectangle(frame, (x1,y1), (x2, y2), (0,255,0), 2)
            sleep(1) 
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

def zoom(frame, zoom_factor=2):
    x_size, y_size = (len(frame), len(frame[0]))
    cropped = frame[int(x_size/2 - x_size/2/zoom_factor):int(x_size/2 + x_size/2/zoom_factor),
                    int(y_size/2 - y_size/2/zoom_factor):int(y_size/2 + y_size/2/zoom_factor)]
    return cv2.resize(cropped, None, fx=zoom_factor, fy=zoom_factor)

def box_faces(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    # Draw rectangle around the faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
    return frame


def rectangle_bounce(current_x, current_y):
    current_x += random.randint(0, 15) - 7
    current_y += random.randint(0, 15) - 7
    if current_x < 0:
        current_x = 0
    if current_y < 0:
        current_y = 0
    if current_x > 300:
        current_x = 300
    if current_y > 300:
        current_y = 300
    return current_x, current_y
    

def gen():
    """Video streaming generator function."""
    frame = cv2.imread("bee.jpg")
    frame = cv2.resize(frame, (0,0), fx=1, fy=1) 

    response = requests.get("http://localhost:8080/bee/beeInfo")
    x1,y1,x2,y2,angle,lat,long = beeInfoParser(response)
    # sleep(1)
    frame = cv2.rectangle(frame, (x1,y1), (x2, y2), (0,255,0), 2)
    # frame = cv2.rectangle(frame, (20,20), (50, 50), (0,255,0), 2)
    frame = cv2.imencode('.jpg', frame)[1].tobytes()
    
    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def beeInfoParser(response): # TODO fix to split
    args = []
    current = ""
    for c in response.text:
        if c == ",":
            args.append(current)
            current = ""
        else:
            current+=c
    args.append(current)
    x1,y1,x2,y2,= [int(i) for i in args[0:4]]
    angle,lat,long = [float(i) for i in args[4:]]
    print(f"{x1=}, {y1=},{x2=},{y2=}, {angle=}, {lat=}, {long=}")
    return (x1,y1,x2,y2,angle,lat,long)

if __name__ == "__main__":
    app.run(debug=True)

