import socket
import time
import pickle
import cv2
import numpy as np

import csv

MAX_BEES = 8 
HEADERSIZE = 64
# [x,y,isRun,angle,lat,long] e

LOCATION_FILE_NAME = "C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\\WaggleDance_1_Locations.csv"
RUN_DATA_FILE_NAME = ""
TEST_MP4_FILE_NAME = "C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\\WaggleDance_1.mp4"

def extract_data():
    #reads the csv file, outputs a 3d numpy matrix
    full_data = []
    with open(LOCATION_FILE_NAME, 'r') as file:
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

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 5050))
s.listen(5)


full_data = extract_data()
counter = 0
video = cv2.VideoCapture(TEST_MP4_FILE_NAME)

while True:
    clientsocket, address = s.accept()
    print(f"Connection from {address} has been established.")

    #increments counter for finding correct frame, loops if at end of data
    if counter < len(full_data) - 1:
        counter += 1
    else:
        counter = 0  
        video = cv2.VideoCapture(TEST_MP4_FILE_NAME)

    success, d = video.read()
    
    matrix = full_data[counter] #8 x 7 array
    #d = cv2.imread("C:\\Users\\theca\\OneDrive\\Desktop\\IDeA Labs\\Bee Research\\beeapp\\beeapp\\test_data\\test.jpg",3)
    
    
    # print(d)
    mat_msg = pickle.dumps(matrix)
   
    img_msg = pickle.dumps(d)
    header= f"{len(img_msg)}:{len(mat_msg)}"
    print(f"{header=}")
    padding_size = HEADERSIZE-len(header)
    padding = " "*padding_size
    # print(f"{padding=}")
    msg = bytes(f"{header}{padding}", 'utf-8')+img_msg+mat_msg

    print(f"{len(mat_msg)=}+{len(img_msg)=}+header={len(header)+padding_size=} total:{len(img_msg)+len(mat_msg)+len(header)}")
    clientsocket.send(msg)