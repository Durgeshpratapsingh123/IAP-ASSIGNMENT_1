import socket
import ssl
import threading

HOST = "127.0.0.1"
PORT = 9000

def receive(sock):
    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                break
            print(msg.decode().strip())
        except:
            break

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock = context.wrap_socket(sock)

sock.connect((HOST, PORT))

threading.Thread(target=receive, args=(sock,), daemon=True).start()

while True:
    msg = input()
    sock.sendall(msg.encode())