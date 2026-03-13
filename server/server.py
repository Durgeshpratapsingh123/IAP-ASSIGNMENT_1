import socket
import threading
import time
import json
import bcrypt
import os
import ssl
import redis

HOST = "0.0.0.0"
PORT = 9000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# Redis connection
r = redis.Redis(host="redis", port=6379, decode_responses=True)

clients = {}           # socket -> username
active_users = {}      # username -> socket
subscriptions = {}     # publisher -> set(subscribers)

lock = threading.Lock()

# ---------------- AUTH ----------------

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

users = load_users()

def authenticate(username, password):
    return username in users and bcrypt.checkpw(
        password.encode(),
        users[username].encode()
    )

# ---------------- UTIL ----------------

def send(sock, message):
    try:
        sock.sendall((message + "\n").encode())
    except:
        pass

# ---------------- REDIS ROOM MANAGEMENT ----------------

def join_room(username, room):

    old_room = r.hget("user_rooms", username)

    if old_room:
        r.srem(f"room:{old_room}", username)

    r.sadd(f"room:{room}", username)
    r.hset("user_rooms", username, room)

def get_room(username):
    return r.hget("user_rooms", username)

def list_rooms():
    keys = r.keys("room:*")
    return [k.split(":")[1] for k in keys]

# ---------------- REDIS PUBSUB ----------------

def redis_listener():

    pubsub = r.pubsub()
    pubsub.subscribe("chat")

    for message in pubsub.listen():

        if message["type"] != "message":
            continue

        data = json.loads(message["data"])

        publisher = data["user"]
        text = data["msg"]

        with lock:
            subs = subscriptions.get(publisher, set())

            for user in subs:
                sock = active_users.get(user)
                if sock:
                    send(sock, f"[{time.strftime('%H:%M:%S')}] {publisher}: {text}")

# ---------------- CLIENT THREAD ----------------

def handle_client(sock, addr):

    send(sock, "[SERVER] LOGIN <username> <password>")

    username = None

    try:

        data = sock.recv(1024).decode().strip()
        parts = data.split()

        if len(parts) != 3 or parts[0] != "LOGIN":
            send(sock, "Invalid login")
            return

        _, username, password = parts

        if not authenticate(username, password):
            send(sock, "Auth failed")
            return

        with lock:

            if username in active_users:
                old = active_users[username]
                send(old, "Logged out due to new login")
                old.close()

            clients[sock] = username
            active_users[username] = sock

        join_room(username, "lobby")

        send(sock, "Login successful")

        while True:

            try:
                data = sock.recv(1024)
                if not data:
                    break
            except:
                break

            msg = data.decode().strip()

            # -------- JOIN ROOM --------

            if msg.startswith("/join "):
                room = msg.split()[1]
                join_room(username, room)
                send(sock, f"[SERVER] Joined {room}")
                continue

            # -------- LIST ROOMS --------

            if msg == "/rooms":
                send(sock, str(list_rooms()))
                continue

            # -------- SUBSCRIBE --------

            if msg.startswith("/subscribe "):

                target = msg.split()[1]

                with lock:

                    if target not in subscriptions:
                        subscriptions[target] = set()

                    subscriptions[target].add(username)

                send(sock, f"[SERVER] Subscribed to {target}")
                continue

            # -------- UNSUBSCRIBE --------

            if msg.startswith("/unsubscribe "):

                target = msg.split()[1]

                with lock:
                    if target in subscriptions:
                        subscriptions[target].discard(username)

                send(sock, f"[SERVER] Unsubscribed from {target}")
                continue

            # -------- PUBLISH MESSAGE --------

            payload = {
                "user": username,
                "msg": msg
            }

            r.publish("chat", json.dumps(payload))

    finally:

        with lock:
            clients.pop(sock, None)
            active_users.pop(username, None)

        if username:
            room = get_room(username)
            if room:
                r.srem(f"room:{room}", username)

        sock.close()

# ---------------- SERVER ----------------

def start_server():

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("cert.pem", "key.pem")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    server = context.wrap_socket(server, server_side=True)

    print("Secure chat server started")

    threading.Thread(target=redis_listener, daemon=True).start()

    while True:

        sock, addr = server.accept()

        threading.Thread(
            target=handle_client,
            args=(sock, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    start_server()