# 📡 Assignment 1 – Internet Architecture and Protocols (CS60008)
# NAME : DURGESH PRATAP SINGH (25CS60R78)
# NAME : SHIVANSH MAURYA (25CS60R57)
# NAME : SHIVAM RANA (25CS60R76)

## Threaded Chat Server with Authentication, Rooms, and Publish–Subscribe

**Language:** Python 3.9+  
**Course:** Internet Architecture and Protocols (CS60008)  
**Assignment:** Assignment–1  

---

## 1. Introduction

This project implements a **TCP-based multi-client chat system** using **Python sockets and threading**, as required for Assignment–1 of the course *Internet Architecture and Protocols (CS60008)*.

The system is developed incrementally to demonstrate core networking and systems concepts including:

- Blocking I/O
- Thread-based concurrency
- Secure authentication
- Session management
- Duplicate login handling
- Chat rooms
- Publish–Subscribe communication model

⚠️ **Scope of this README**  
This document describes the implementation **up to Problem-5 (Publish–Subscribe)**.  
**Redis-based distributed state (Problem-6)** and later components are intentionally excluded.

---

## 2. Technologies Used

- **Python 3.9+**
- Standard libraries:
  - socket
  - threading
  - time
  - json
  - os
- External library:
  - bcrypt (for secure password hashing)

No high-level frameworks such as FastAPI, asyncio, or WebSockets are used, in strict compliance with assignment constraints.

---

## 3. Project Structure

ASSIGNMENT_1/
│
├── client/
│   └── client.py              # TCP-based chat client
│
├── server/
│   ├── server.py              # Server entry point (listener + thread creation)
│   ├── client_handler.py      # Per-client logic and protocol handling
│   └── users.json             # User credentials (bcrypt-hashed)
│
└── README.md

---

## 4. Design Overview

The server is deliberately split into two components to improve modularity and clarity.

### 4.1 server.py – Server Entry Point

Responsibilities:
- Create and bind the TCP socket
- Listen for incoming client connections
- Accept connections using socket.accept()
- Spawn one thread per client
- Delegate all client-specific logic to client_handler.py

This file contains no application logic and focuses purely on connection management.

---

### 4.2 client_handler.py – Core Server Logic

Responsibilities:
- Authentication and session creation
- Duplicate login handling
- Chat room management
- Publish–Subscribe logic
- Message routing
- Client cleanup on disconnect

This separation reflects real-world server design and simplifies future extensions such as Redis and TLS.

---

## 5. How to Run the Project

### 5.1 Start the Server

cd server  
python server.py

Expected output:  
[*] Chat server running on port 9000

---

### 5.2 Start a Client

cd client  
python client.py

---

## 6. Client–Server Protocol

### 6.1 Authentication Protocol

On connection, the server sends:

[SERVER] Login using: LOGIN <username> <password>

The client must respond exactly in the following format:

LOGIN DPS password123

Rules:
- Invalid format → connection closed
- Invalid credentials → connection closed
- Valid credentials → authenticated session created

Passwords are never stored or transmitted in plaintext.

---

## 7. Problem-1: Thread-Based Chat Server

Objective: Implement a thread-per-client TCP server using blocking I/O.

Features:
- One thread per client
- Graceful handling of client disconnects
- Clear server-side logging

---

## 8. Problem-2: Authentication

- Credentials stored in users.json
- Passwords hashed using bcrypt
- Authentication enforced immediately after connection

---

## 9. Problem-3: Duplicate Login Handling

Policy: Force Logout Existing Session

If a user logs in while another session is active, the existing session is terminated and the new login succeeds.

---

## 10. Problem-4: Chat Rooms

Supported commands:
- /join <room>
- /leave
- /rooms

Each client belongs to exactly one room. Default room is lobby.

---

## 11. Problem-5: Publish–Subscribe Model

Supported commands:
- /subscribe <user>
- /unsubscribe <user>
- /subs

Messages are delivered only to subscribed clients. Message ordering is preserved per publisher.

---

## 12. Thread Safety

All shared state is protected using threading.Lock to avoid race conditions.

---

## 13. Limitations (Before Redis)

- In-memory state only
- Single server instance
- No fault tolerance

---

## 14. Conclusion

This implementation demonstrates a complete threaded chat server with authentication, rooms, and publish–subscribe messaging, forming a strong foundation for distributed extensions using Redis.
