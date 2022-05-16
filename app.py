from math import sin, cos, pi, pow, sqrt
import csv
from re import X
import cv2
import random
from flask import Flask, render_template, Response, request
import requests


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


app = create_app()

camera = cv2.VideoCapture(0)


def gen():  ## For images
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


#Input: jpeg, x, y, angle = None, length = None, lat = None, long = None, on_run = False
#Functionality: rend jpeg, draw box centered on (x,y), if angle/length != None draw arrow
#               if lat and long != None draw 
#Global: save the first recieved point on the run as start point on the arrow, replace as
#        another run is started. Save points thusfar to show waggle points to help with visualization (draw points on adjacent ones)
def gen_frames_advanced():
    #used for saving points as we go
    run_points = []
    returning = False
    response = []
    response.append(150)
    response.append(150)
    response.append(1)

    while True:
        response = simulateResponse(response)
        frame, x ,y ,angle ,length, lat, long, on_run = simulateParsing(response)
        response[0] = x
        response[1] = y
        if on_run:
            if returning:
                returning = False
                run_points = []
            run_points.append((x,y))
        else:
            returning = True
        for point in run_points:
            cv2.circle(frame, point, 1, (255,100,0), -1)
        cv2.rectangle(frame, (x-100,y-100), (x+100, y+100), (0,255,0), 2)
        if angle != None and length != None:
            #TODO - FIX DUMMY VARIABLES
            x_start, y_start = x, y
            draw_arrow(frame, angle, x_start, y_start, length)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def gen_frames():   # for camera
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            zoom(frame, 1)
            frame = rescale_frame(frame,100)
            #frame = box_faces(frame)
            #response = requests.get("http://localhost:8080/beeInfo")
            x,y,angle,lat,long = 100, 100, 100, 100, 100 #beeInfoParser(response)
            frame = cv2.rectangle(frame, (x-20,y-20), (x+20, y+20), (0,255,0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


def gen_frames_demo():   # from csv and mp4 files
    run = 0
    frame_num = 0
    scale = 65
    run_info, box = read_locations()
    x_min = int(box[0]*scale/100)
    y_min = int(box[1]*scale/100)
    x_max = int(box[2]*scale/100)
    y_max = int(box[3]*scale/100)
    end_frame, x, y, angle, length = run_info[run]
    x = int(x*scale/100)
    y = int(y*scale/100)

    cap = cv2.VideoCapture("C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\\WaggleDance_1.mp4")

    while True:
        success, frame = cap.read()  # read the camera frame
        cv2.waitKey(20)
        if not success:
            break
        else:
            zoom(frame, 1)
            frame = rescale_frame(frame,scale)

            if end_frame == frame_num:
                run += 1
                if run < len(run_info):
                    end_frame, x, y, angle, length = run_info[run]
                    x = int(x*scale/100)
                    y = int(y*scale/100)
                else:
                    run, frame_num = 0, 0 #used for looping in testing

            cv2.rectangle(frame, (x_min-40,y_min-40), (x_max+40, y_max+40), (0,255,0), 2)
            draw_arrow(frame, angle, x, y, length)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            frame_num += 1
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


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


#The current version only works on my (Caelen's) Computer due to file path issues
def read_locations(location_file_name = "C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\\WaggleDance_1_Locations.csv", 
                    run_data_file_name = "C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\WaggleDance_1_Runs.csv"):
    #Call this method once, extract relevant information from the csv file
    locations = []
    max_x, max_y, min_x, min_y = 0, 0, 10000, 10000
    with open(location_file_name, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            locations.append(row)
            x = int(float(row[1]))
            if x > max_x:
                max_x = x
            if x < min_x:
                min_x = x
            y = int(float(row[2]))
            if y > max_y:
                max_y = y
            if y < min_y:
                min_y = y
    runs = []
    with open(run_data_file_name, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            if not row[3] == '':
                run = [None] * 5
                run[0] = int(row[2]) #end_frame
                run[1] = int(float(locations[int(row[1])][1])) #start_x
                run[2] = int(float(locations[int(row[1])][2])) #start_y
                run[3] = float(row[3]) #angle
                #uses distance formula to find length
                length = sqrt(pow(run[1] - float(locations[int(row[2])][1]),2) + pow(run[2] - float(locations[int(row[2])][2]), 2))
                run[4] = length
                runs.append(run)

    #[end_frame, start_x, start_y, angle, length]
    return runs, (min_x, min_y, max_x, max_y)

    
def rescale_frame(frame, percent=75):
    '''Rescales the frame to a percentage of its original size'''
    width = int(frame.shape[1] * percent/ 100)
    height = int(frame.shape[0] * percent/ 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)


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


#response of format [x, y, direction, timer]
def simulateParsing(response):
    #simulates and returns info from the backend
    success, frame = camera.read()
    if success:
        #fake data based on fake response
        x, y, angle, length, lat, longit, on_run = response[0], response[1], None, None, None, None, True
        x += response[2] * random.randint(10,25)
        y += random.randint(3,7)
        return frame, x, y, angle, length, lat, longit, on_run

def simulateResponse(response):
    response[2] = response[2] * -1
    return response



if __name__ == "__main__":
    app.run(debug=True)

