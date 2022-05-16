import socket
from unittest.util import _MAX_LENGTH

HEADER = 64  # every message has a header of length 64 bytes, may need to be more
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
MAX_LENGTH = 2048

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(MAX_LENGTH).decode(FORMAT))

send("Hello world!")
input()
send("Hello everyone!")
input()
send("Hello bees!")
send(DISCONNECT_MESSAGE)