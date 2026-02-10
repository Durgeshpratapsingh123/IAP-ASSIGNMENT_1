# import socket
# import threading
# import time

# HOST = "0.0.0.0"
# PORT = 9000

# clients = {}          # socket -> username
# lock = threading.Lock()


# def send(sock, message):
#     try:
#         sock.sendall((message + "\n").encode())
#     except:
#         pass


# def broadcast(message, exclude=None):
#     with lock:
#         for sock in list(clients):
#             if sock != exclude:
#                 try:
#                     send(sock, message)
#                 except:
#                     sock.close()
#                     clients.pop(sock, None)


# def handle_client(sock, addr):
#     print(f"[+] New connection from {addr[0]}:{addr[1]}")

#     send(sock, "[SERVER] Welcome to the chat server")
#     send(sock, "[SERVER] Enter your username:")

#     try:
#         username = sock.recv(1024).decode().strip()
#         if not username:
#             sock.close()
#             return

#         with lock:
#             clients[sock] = username

#         print(f"[+] User '{username}' connected from {addr[0]}:{addr[1]}")
#         broadcast(f"🟢 {username} joined the chat")

#         send(sock, "[SERVER] You can start typing messages")

#         while True:
#             data = sock.recv(1024)
#             if not data:
#                 break

#             msg = data.decode().strip()
#             if not msg:
#                 continue

#             timestamp = time.strftime("%H:%M:%S")
#             broadcast(f"[{timestamp}] {username}: {msg}", sock)

#     except Exception as e:
#         print(f"[!] Error with {addr}: {e}")

#     finally:
#         with lock:
#             username = clients.pop(sock, "Unknown")

#         print(f"[-] User '{username}' disconnected from {addr[0]}:{addr[1]}")
#         broadcast(f"🔴 {username} left the chat")
#         sock.close()


# def start_server():
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind((HOST, PORT))
#     server.listen()

#     print(f"[*] Chat server running on port {PORT}")

#     while True:
#         sock, addr = server.accept()
#         threading.Thread(
#             target=handle_client,
#             args=(sock, addr),
#             daemon=True
#         ).start()


# if __name__ == "__main__":
#     start_server()

import socket
import threading
import time
import json
import bcrypt
import os

HOST = "0.0.0.0"
PORT = 9000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

clients = {}          # socket -> username
active_users = {}    # username -> socket
user_rooms = {}      # socket -> room
rooms = {"lobby": set()}

subscriptions = {}   # publisher -> set(subscribers)

lock = threading.Lock()


# ---------- AUTH ----------

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

users = load_users()


def authenticate(username, password):
    return username in users and bcrypt.checkpw(
        password.encode(), users[username].encode()
    )


# ---------- MESSAGING ----------

def send(sock, message):
    try:
        sock.sendall((message + "\n").encode())
    except:
        pass


def send_to_subscribers(publisher, message):
    with lock:
        subs = subscriptions.get(publisher, set()).copy()

    for subscriber in subs:
        sock = active_users.get(subscriber)
        if sock:
            send(sock, message)


# ---------- SUBSCRIPTION HELPERS ----------

def subscribe(subscriber, publisher):
    with lock:
        if publisher not in active_users:
            return False

        subscriptions.setdefault(publisher, set()).add(subscriber)
    return True


def unsubscribe(subscriber, publisher):
    with lock:
        subscriptions.get(publisher, set()).discard(subscriber)


def list_subscriptions(user):
    with lock:
        pubs = [
            pub for pub, subs in subscriptions.items() if user in subs
        ]
    return pubs


# ---------- CLIENT HANDLER ----------

def handle_client(sock, addr):
    print(f"[+] New connection from {addr[0]}:{addr[1]}")

    send(sock, "[SERVER] Welcome to the chat server")
    send(sock, "[SERVER] Login using: LOGIN <username> <password>")

    try:
        data = sock.recv(1024).decode().strip()
        parts = data.split()

        if len(parts) != 3 or parts[0] != "LOGIN":
            send(sock, "[ERROR] Invalid login format")
            sock.close()
            return

        _, username, password = parts

        if not authenticate(username, password):
            send(sock, "[ERROR] Authentication failed")
            sock.close()
            return

        # ----- FORCE LOGOUT -----
        with lock:
            if username in active_users:
                old_sock = active_users[username]
                send(old_sock, "[SERVER] Logged out due to new login")
                old_sock.close()

            clients[sock] = username
            active_users[username] = sock
            rooms["lobby"].add(sock)
            user_rooms[sock] = "lobby"

        print(f"[+] User '{username}' authenticated")
        send(sock, "[SERVER] Login successful")
        send(sock, "[SERVER] Commands: /subscribe <user>, /unsubscribe <user>, /subs")

        # ----- MAIN LOOP -----
        while True:
            data = sock.recv(1024)
            if not data:
                break

            msg = data.decode().strip()
            if not msg:
                continue

            # ----- SUB COMMANDS -----
            if msg.startswith("/subscribe "):
                target = msg.split(maxsplit=1)[1]
                if subscribe(username, target):
                    send(sock, f"[SERVER] Subscribed to {target}")
                else:
                    send(sock, "[ERROR] User not online")
                continue

            if msg.startswith("/unsubscribe "):
                target = msg.split(maxsplit=1)[1]
                unsubscribe(username, target)
                send(sock, f"[SERVER] Unsubscribed from {target}")
                continue

            if msg == "/subs":
                pubs = list_subscriptions(username)
                send(sock, f"[SERVER] Subscriptions: {', '.join(pubs) or 'none'}")
                continue

            # ----- PUBLISH MESSAGE -----
            ts = time.strftime("%H:%M:%S")
            send_to_subscribers(
                username,
                f"[{ts}] {username}: {msg}"
            )

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")

    finally:
        with lock:
            username = clients.pop(sock, None)
            user_rooms.pop(sock, None)

            if username and active_users.get(username) == sock:
                active_users.pop(username)

            for subs in subscriptions.values():
                subs.discard(username)

        print(f"[-] User '{username}' disconnected")
        sock.close()


# ---------- SERVER LOOP ----------

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[*] Chat server running on port {PORT}")

    while True:
        sock, addr = server.accept()
        threading.Thread(
            target=handle_client,
            args=(sock, addr),
            daemon=True
        ).start()


if __name__ == "__main__":
    start_server()
