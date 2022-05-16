import socket
import pickle

from numpy import full
import cv2

HEADERSIZE = 64
BLOCK_SIZE = 4096

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((socket.gethostname(), 5050))

while True:
    full_msg = b''
    new_msg = True
    while True:
        msg = s.recv(BLOCK_SIZE)
        if new_msg:
            # print(f"{msg.decode()=}")
            print(f"{msg[:HEADERSIZE]}")
            imglen, matlen = [int(i) for i in msg[:HEADERSIZE].decode().split(":")]
            new_msg = False
            print(f"{imglen=}, {matlen=}, total={imglen+matlen+HEADERSIZE}")

        full_msg += msg
        print(f"Received: {len(full_msg)} bytes out of {imglen+matlen+HEADERSIZE}")
        if len(full_msg)== imglen+matlen+HEADERSIZE:
            print("full msg recvd")
            print(full_msg[HEADERSIZE:])
            img_bytes = pickle.loads(full_msg[HEADERSIZE:HEADERSIZE+imglen])
            mat_bytes = pickle.loads(full_msg[HEADERSIZE+imglen:])
            print(mat_bytes)
            cv2.imwrite("recived.png",img_bytes)
            new_msg = True
            full_msg = b""