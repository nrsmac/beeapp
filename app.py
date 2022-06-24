from math import sin, cos, pi, pow, sqrt
from re import X
from flask import Flask, render_template, Response, request
from regex import W
from numpy import full, shape

import time
import cv2
import socket
import pickle
import threading

HEADERSIZE = 64
BLOCK_SIZE = 16348
RECTANGLE_WIDTH = 150
SCALE = 60 #percentage
FRAME_RECEIVED_MSG = "!FRAME_RECEIVED"
DISCONNECT_MESSAGE = "!DISCONNECT".encode('utf-8')

SERVER_PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, SERVER_PORT)

n_frames = None


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
        
        return Response(gen_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/map', methods=['POST', 'GET'])
    def mapview():

        return render_template('map.html')

    @app.route('/combined', methods=['POST', 'GET'])
    def combinedview():

        return render_template('combined.html')
        
    return app


def gen_frames():
    #used for saving points as we go
    run_points = []
    returning = False
    seconds = [] # Seconds is a buffer that is populated in a background thread, receive_thread
    frame, x, y, isRun, angle, magnitude, latitude, longitude = None, None, None, None, None, None, None, None
    start_time = time.time() # start time of the loop
    client = connect_to_server()
    receiving_thread = threading.Thread(target=receive_stream, args=(client, seconds))
    receiving_thread.start()

    time.sleep(1)  # makes it more likely that seconds is already populated
    while seconds:
        for frame_with_data in seconds.pop(0):
            frame, mat_bytes = frame_with_data 

            #Initialize run 
            run = mat_bytes[0]
            x = int(run[0])
            y = int(run[1])
            isRun = run[2]
            angle = run[3]
            magnitude = run[4]
            latitude = run[5]
            longitude = run[6]

            frame = zoom(frame, SCALE/100)
            x = int(x * SCALE/100)
            y = int(y * SCALE/100)
            magnitude = magnitude * SCALE / 100

            if isRun:
                if returning:
                    returning = False
                    run_points = []
                run_points.append((x,y))
            else:
                returning = True

            for point in run_points:
                cv2.circle(frame, point, 2, (0,0,255), -1)
            cv2.rectangle(frame, (x-RECTANGLE_WIDTH//2,y-RECTANGLE_WIDTH//2), (x+RECTANGLE_WIDTH//2, y+RECTANGLE_WIDTH//2), (0,255,0), 2)

            if angle != None and magnitude != None:
                #TODO - FIX DUMMY VARIABLES
                x_start, y_start = x, y
                draw_arrow(frame, angle, x_start, y_start, magnitude)

            # Encode and write image to webpage
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.033333333333) # TODO: will this cause issues? Will the lag just get worse each time?  


def zoom(frame, zoom_factor=2):
    x_size, y_size = (len(frame), len(frame[0]))
    # cropped = frame[int(x_size/2 - x_size/2/zoom_factor):int(x_size/2 + x_size/2/zoom_factor),
                    # int(y_size/2 - y_size/2/zoom_factor):int(y_size/2 + y_size/2/zoom_factor)]
    return cv2.resize(frame, None, fx=zoom_factor, fy=zoom_factor)


def draw_arrow(frame, angle, x_start, y_start, length = 20):
    '''Draws an arrow on a frame based on the input origin, angle, and length'''
    angle = (angle - 90)/180 * pi
    x_end = x_start + int(cos(angle) * length)
    y_end = y_start + int(sin(angle) * length)
    cv2.arrowedLine(frame, (x_start,y_start), (x_end,y_end),(255,0,0), 2)

    
def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    return client


def rescale_frame(frame, percent=75):
    '''Rescales the frame to a percentage of its original size'''
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)

def receive_stream(client, seconds):
    while True:
        second = receive_second(client)
        if second == None:
            return None
        seconds.append(second)

def receive_second(client):
    '''Receives 30 frames from server. Blocks until 30 frames have been received.'''
    frames_with_data = []
    
    while len(frames_with_data) < 30:
        response = receive_frame(client)
        if response is None:
            return None
        img_bytes, mat_bytes = response 
        frames_with_data.append((img_bytes, mat_bytes))
    
    return frames_with_data

def receive_frame(client):
    '''Receives one frame from server over client socket'''
    full_msg = b''
    new_msg = True
    while True:
        msg = client.recv(BLOCK_SIZE)
        if msg == DISCONNECT_MESSAGE:
            client.close()
            print("SERVER DISCONNECTED")
            return None

        if new_msg:
            n_frames, imglen, matlen = [int(i) for i in msg[:HEADERSIZE].decode().split(":")]
            new_msg = False

        full_msg += msg
        #print(f"Frame:{n_frames} Received: {len(full_msg)} bytes out of {imglen+matlen+HEADERSIZE}")
        if len(full_msg) >= imglen+matlen+HEADERSIZE:
            # print("full msg recvd")
            #print(full_msg[HEADERSIZE:])
            img_bytes = pickle.loads(full_msg[HEADERSIZE:HEADERSIZE+imglen])
            mat_bytes = pickle.loads(full_msg[HEADERSIZE+imglen:])
            #print(mat_bytes)
            #cv2.imwrite("recived.png",img_bytes)
            new_msg = True
            full_msg = b""
            client.send(FRAME_RECEIVED_MSG.encode('utf-8'))
            return img_bytes, mat_bytes


if __name__ == "__main__":
    app.run(debug=True)
