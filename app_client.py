from math import sin, cos, pi, pow, sqrt
from re import X
import cv2
import random
from flask import Flask, render_template, Response, request
import requests
import time

import socket
import pickle
from numpy import full, shape

HEADERSIZE = 64
BLOCK_SIZE = 4096
RECTANGLE_WIDTH = 150
SCALE = 75 #percentage


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
        
        return Response(gen_frames_advanced(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/map', methods=['POST', 'GET'])
    def mapview():

        return render_template('map.html')

    @app.route('/combined', methods=['POST', 'GET'])
    def combinedview():

        return render_template('combined.html')
        
    return app

cam = cv2.VideoCapture(0)

#Need to take test csv data, put into numpy array, format "response" with that and a frame, and process it correctly
def gen_frames_advanced():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 5050))

    #used for saving points as we go
    run_points = []
    returning = False
    frame, x, y, isRun, angle, magnitude, latitude, longitude = None, None, None, None, None, None, None, None

    while True:
        #if frame == None: #in place to prevent permanently waiting for the server on second request
        new_frame, mat_bytes = requestFromServer(s)
        if new_frame != None:
            print("Empty Frame")
            frame = new_frame

            #initialize new runpoints array if not already one?
            #for run in mat_bytes:
            run = mat_bytes[0]
            x = int(run[0])
            y = int(run[1])
            isRun = run[2]
            angle = run[3]
            magnitude = run[4]
            latitude = run[5]
            longitude = run[6]

        #rescale_frame(frame, SCALE)
        #x = int(x * (SCALE/100))
        #y = int(y * (SCALE/100))
        
        if isRun:
            if returning:
                returning = False
                run_points = []
            run_points.append((x,y))
        else:
            returning = True

        for point in run_points:
            cv2.circle(frame, point, 1, (255,100,0), -1)
        cv2.rectangle(frame, (x-RECTANGLE_WIDTH//2,y-RECTANGLE_WIDTH//2), (x+RECTANGLE_WIDTH//2, y+RECTANGLE_WIDTH//2), (0,255,0), 2)

        if angle != None and magnitude != None:
            #TODO - FIX DUMMY VARIABLES
            x_start, y_start = x, y
            draw_arrow(frame, angle, x_start, y_start, magnitude)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def zoom(frame, zoom_factor=2):
    x_size, y_size = (len(frame), len(frame[0]))
    cropped = frame[int(x_size/2 - x_size/2/zoom_factor):int(x_size/2 + x_size/2/zoom_factor),
                    int(y_size/2 - y_size/2/zoom_factor):int(y_size/2 + y_size/2/zoom_factor)]
    return cv2.resize(cropped, None, fx=zoom_factor, fy=zoom_factor)


def draw_arrow(frame, angle, x_start, y_start, length = 20):
    '''Draws an arrow on a frame based on the input origin, angle, and length'''
    angle = (angle - 90)/180 * pi
    x_end = x_start + int(cos(angle) * length)
    y_end = y_start + int(sin(angle) * length)
    cv2.arrowedLine(frame, (x_start,y_start), (x_end,y_end),(255,0,0), 2)

    
def rescale_frame(frame, percent=75):
    '''Rescales the frame to a percentage of its original size'''
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)


def requestFromServer(server_socket):
        full_msg = b''
        new_msg = True
    #while True:
        msg = server_socket.recv(BLOCK_SIZE)
        if new_msg:
            # print(f"{msg.decode()=}")
            #print(f"{msg[:HEADERSIZE]}")
            imglen, matlen = [int(i) for i in msg[:HEADERSIZE].decode().split(":")]
            new_msg = False
            #print(f"{imglen=}, {matlen=}, total={imglen+matlen+HEADERSIZE}")

        full_msg += msg
        #print(f"Received: {len(full_msg)} bytes out of {imglen+matlen+HEADERSIZE}")
        if len(full_msg)== imglen+matlen+HEADERSIZE:
            print("full msg recvd")
            #print(full_msg[HEADERSIZE:])
            img_bytes = pickle.loads(full_msg[HEADERSIZE:HEADERSIZE+imglen])
            mat_bytes = pickle.loads(full_msg[HEADERSIZE+imglen:])
            #print(mat_bytes)
            #cv2.imwrite("recived.png",img_bytes)
            new_msg = True
            full_msg = b""
            return img_bytes, mat_bytes


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

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)