from http import client
import socket
import threading
import time
import pickle
import cv2
import numpy as np

import csv

MAX_BEES = 8 
HEADERSIZE = 64

PORT=5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FRAME_RECEIVED_MSG = "!FRAME_RECEIVED"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
# [x,y,isRun,angle,lat,long] e

LOCATIONS_FILE_NAME = "./test_data/WaggleDance_1_Locations.csv"
RUN_DATA_FILE_NAME = ""
TEST_MP4_FILE_NAME = "./test_data/WaggleDance_1.mp4"

def load_location_data(path):
    #reads the csv file, outputs a 3d numpy matrix
    full_data = []
    with open(path, 'r') as file:
        csvreader = csv.reader(file) #read file
        header = next(csvreader) #remove the data header
        for row in csvreader:
            next_frame_data = np.empty((MAX_BEES, 7))
            next_frame_data.fill(-1)
            next_frame_data[0][0] = int(float(row[1])) #x data
            next_frame_data[0][1] = int(float(row[2])) #y data
            next_frame_data[0][2] = int(float(row[3])) #isRun data, stored as 1 or 0
            next_frame_data[0][3] = 30 #placeholder angle
            next_frame_data[0][4] = 20 #placeholder magnitude
            next_frame_data[0][5] = None #latitude
            next_frame_data[0][6] = None #longitude
            full_data.append(next_frame_data)
    return np.asarray(full_data)

def createMessage(counter, frame, matrix):
    mat_msg = pickle.dumps(matrix)
    
    img_msg = pickle.dumps(frame)
    header= f"{counter}:{len(img_msg)}:{len(mat_msg)}"
    # print(f"{header=}")
    padding_size = HEADERSIZE-len(header)
    padding = " "*padding_size
        # print(f"{padding=}")
    msg = bytes(f"{header}{padding}", 'utf-8')+img_msg+mat_msg
    # print(f"{len(mat_msg)=}+{len(img_msg)=}+header={len(header)+padding_size=} total:{len(img_msg)+len(mat_msg)+len(header)}")

    return msg

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True

    location_data = load_location_data(LOCATIONS_FILE_NAME) 
    video = cv2.VideoCapture(TEST_MP4_FILE_NAME)
    counter = 0 
    while True:
        #increments counter for finding correct frame, loops if at end of data
        success, frame = video.read()       
        if success:
            msg = createMessage(counter, frame, location_data[counter])
            conn.send(msg) 
            m = conn.recv(64).decode('utf-8')
            print(m)
            if m == FRAME_RECEIVED_MSG:
                counter += 1
            if m == DISCONNECT_MESSAGE:
                break
        else:
            break
    conn.send(DISCONNECT_MESSAGE.encode('utf-8'))
    conn.close()
    

def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn,addr))
        thread.start()

start()