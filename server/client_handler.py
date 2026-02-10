import time
import json
import bcrypt
import threading

USERS_FILE = "server/users.json"

clients = {}          # socket -> username
lock = threading.Lock()


# ---------- AUTH ----------

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

users = load_users()


def authenticate(username, password):
    if username not in users:
        return False
    return bcrypt.checkpw(password.encode(), users[username].encode())


# ---------- MESSAGING ----------

def send(sock, msg):
    try:
        sock.sendall((msg + "\n").encode())
    except:
        pass


def broadcast(message, exclude=None):
    with lock:
        for s in list(clients):
            if s != exclude:
                try:
                    send(s, message)
                except:
                    s.close()
                    clients.pop(s, None)


# ---------- CLIENT THREAD ----------

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
            print(f"[!] Failed login for '{username}' from {addr}")
            return

        with lock:
            clients[sock] = username

        print(f"[+] User '{username}' authenticated from {addr[0]}:{addr[1]}")
        send(sock, "[SERVER] Login successful")
        broadcast(f"🟢 {username} joined the chat", sock)

        while True:
            data = sock.recv(1024)
            if not data:
                break

            msg = data.decode().strip()
            if not msg:
                continue

            ts = time.strftime("%H:%M:%S")
            broadcast(f"[{ts}] {username}: {msg}", sock)

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")

    finally:
        with lock:
            username = clients.pop(sock, None)

        if username:
            broadcast(f"🔴 {username} left the chat")
            print(f"[-] User '{username}' disconnected")

        sock.close()
