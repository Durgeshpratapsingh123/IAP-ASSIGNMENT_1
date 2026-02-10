# import socket
# import threading

# SERVER_HOST = "127.0.0.1"
# SERVER_PORT = 9000

# def receive_messages(sock):
#     while True:
#         try:
#             msg = sock.recv(1024)
#             if not msg:
#                 break
#             print(msg.decode().rstrip())
#         except:
#             break

# def send_messages(sock):
#     while True:
#         try:
#             msg = input("> ")
#             sock.sendall(msg.encode())
#         except:
#             break

# def main():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect((SERVER_HOST, SERVER_PORT))

#     threading.Thread(
#         target=receive_messages,
#         args=(sock,),
#         daemon=True
#     ).start()

#     send_messages(sock)

# if __name__ == "__main__":
#     main()

import socket
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9000


def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                break
            print("\r" + msg.decode().rstrip())
            print("> ", end="", flush=True)
        except:
            break


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))

    # Server greeting
    print(sock.recv(1024).decode().strip())
    print(sock.recv(1024).decode().strip())

    # Login
    login_cmd = input("> ")
    sock.sendall(login_cmd.encode())

    response = sock.recv(1024).decode()
    print(response)

    if "successful" not in response:
        sock.close()
        return

    # Start receiving messages
    threading.Thread(
        target=receive_messages,
        args=(sock,),
        daemon=True
    ).start()

    # Send messages
    while True:
        msg = input("> ")
        sock.sendall(msg.encode())


if __name__ == "__main__":
    main()
