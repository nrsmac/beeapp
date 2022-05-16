import socket
import time
import pickle
import cv2
import numpy as np

MAX_BEES = 8 
HEADERSIZE = 64
# [x,y,isRun,angle,lat,long] e

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 5050))
s.listen(5)

while True:
    clientsocket, address = s.accept()
    print(f"Connection from {address} has been established.")

    d = cv2.imread("test.png",3)
    matrix = np.array([[-1 for _ in range(5)]]*MAX_BEES)
    matrix[0] = [200,200,0,23.1,40.249633,-111.650916]  
    
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