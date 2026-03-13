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

# ---------- GLOBAL STATE ----------
clients = {}          # socket -> username
active_users = {}     # username -> socket
user_rooms = {}       # socket -> room
rooms = {"lobby": set()}  # room -> set(sockets)
subscriptions = {}    # publisher -> set(subscribers)

lock = threading.Lock()


# ---------- AUTH ----------
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

users = load_users()


def authenticate(username, password):
    return username in users and bcrypt.checkpw(
        password.encode(),
        users[username].encode()
    )


# ---------- UTILITY ----------
def send(sock, message):
    try:
        sock.sendall((message + "\n").encode())
    except:
        pass


def broadcast_room(room, message, exclude=None):
    with lock:
        members = rooms.get(room, set()).copy()

    for member in members:
        if member != exclude:
            send(member, message)


# ---------- ROOM MANAGEMENT ----------
def join_room(sock, username, new_room):
    with lock:
        old_room = user_rooms.get(sock, "lobby")

        if old_room == new_room:
            return f"[SERVER] You are already in room '{new_room}'"

        rooms[old_room].discard(sock)
        rooms.setdefault(new_room, set()).add(sock)
        user_rooms[sock] = new_room

    return f"[SERVER] Joined room '{new_room}'"


def leave_room(sock, username):
    return join_room(sock, username, "lobby")


def list_rooms():
    with lock:
        return ", ".join(rooms.keys())


# ---------- SUBSCRIPTION MANAGEMENT ----------
def subscribe(subscriber, publisher):
    with lock:
        if publisher not in active_users:
            return False

        sub_sock = active_users.get(subscriber)
        pub_sock = active_users.get(publisher)

        if not sub_sock or not pub_sock:
            return False

        # Restrict subscription to same room
        if user_rooms.get(sub_sock) != user_rooms.get(pub_sock):
            return False

        subscriptions.setdefault(publisher, set()).add(subscriber)

    return True


def unsubscribe(subscriber, publisher):
    with lock:
        subscriptions.get(publisher, set()).discard(subscriber)


def list_subscriptions(user):
    with lock:
        return [
            pub for pub, subs in subscriptions.items()
            if user in subs
        ]


def send_to_subscribers(publisher, message):
    with lock:
        subs = subscriptions.get(publisher, set()).copy()

    for subscriber in subs:
        sock = active_users.get(subscriber)
        if sock:
            send(sock, message)


# ---------- CLIENT HANDLER ----------
def handle_client(sock, addr):
    print(f"[+] New connection from {addr[0]}:{addr[1]}")

    send(sock, "[SERVER] Welcome to the chat server")
    send(sock, "[SERVER] Login using: LOGIN <username> <password>")

    username = None

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

        # ----- FORCE LOGOUT EXISTING SESSION -----
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
        send(sock, "[SERVER] Available commands: /join, /leave, /rooms, /subscribe, /unsubscribe, /subs")

        # ----- MAIN LOOP -----
        while True:
            data = sock.recv(1024)
            if not data:
                break

            msg = data.decode().strip()
            if not msg:
                continue

            # ----- ROOM COMMANDS -----
            if msg.startswith("/join "):
                room = msg.split(maxsplit=1)[1]
                response = join_room(sock, username, room)
                send(sock, response)
                continue

            if msg == "/leave":
                response = leave_room(sock, username)
                send(sock, response)
                continue

            if msg == "/rooms":
                send(sock, f"[SERVER] Active rooms: {list_rooms()}")
                continue

            # ----- SUBSCRIPTION COMMANDS -----
            if msg.startswith("/subscribe "):
                target = msg.split(maxsplit=1)[1]
                if subscribe(username, target):
                    send(sock, f"[SERVER] Subscribed to {target}")
                else:
                    send(sock, "[ERROR] Cannot subscribe (user offline or different room)")
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

            # ----- NORMAL MESSAGE (PUBLISH) -----
            ts = time.strftime("%H:%M:%S")
            send_to_subscribers(
                username,
                f"[{ts}] {username}: {msg}"
            )

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")

    finally:
        with lock:
            clients.pop(sock, None)
            room = user_rooms.pop(sock, None)

            if room:
                rooms.get(room, set()).discard(sock)

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

