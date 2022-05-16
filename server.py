import socket
import threading
from dataclasses import dataclass

HEADER = 64  # every message has a header of length 64 bytes, may need to be more
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

@dataclass
class BeeInfo:
    x: int
    y: int
    angle: float
    lat: float
    long: float

examle_bee = BeeInfo(0,0,123.4, 123.4, 123.4)

def get_bee_info():
    if examle_bee.x >= 500:
        examle_bee.x = 0
    else:
        examle_bee.x += 5

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)  # Blocks and receives header
        if msg_length:            
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)  # receive actual message based on length provided in header
            
            if msg== DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr=}] {msg=}")
            conn.send("Message received!".encode(FORMAT))
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn, addr = server.accept() # Blocks
        thread = threading.Thread(target=handle_client, args=(conn,addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

print("[STARTING] server is starting")
start()