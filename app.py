import numpy
import cv2
from flask import Flask, render_template, Response, request
import requests
from time import sleep

def create_app():
    """Initialize the application"""
    app = Flask(__name__)   
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

    @app.route('/map', methods=['POST', 'GET'])
    def mapview():

        return render_template('map.html')

    @app.route('/combined', methods=['POST', 'GET'])
    def combinedview():

        return render_template('combined.html')
        
    return app


app = create_app()

camera = cv2.VideoCapture(0)


def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            frame = zoom(frame, 2)
            #frame = box_faces(frame)
            response = requests.get("http://localhost:8080/bee/beeInfo")
            x,y,angle,lat,long = beeInfoParser(response)
            frame = cv2.rectangle(frame, (x-20,y-20), (x+20, y+20), (0,255,0), 2)
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
    

def gen():
    """Video streaming generator function."""
    frame = cv2.imread("bee.jpg")
    frame = cv2.resize(frame, (0,0), fx=1, fy=1) 

    #response = requests.get("http://localhost:8080/bee/beeInfo")
    x1,y1,x2,y2,angle,lat,long = 100, 100, 150, 150, 30, 100.0, 120.0 #beeInfoParser(response)
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
    x,y= [int(i) for i in args[0:2]]
    angle,lat,long = [float(i) for i in args[2:]]
    print(f"{x=}, {y=}, {angle=}, {lat=}, {long=}")
    return (x, y,angle,lat,long)


if __name__ == "__main__":
    app.run(debug=True)

