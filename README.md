#  Assignment 1 -- Internet Architecture and Protocols (CS60008)

## NAME : DURGESH PRATAP SINGH (25CS60R78)

## NAME : SHIVANSH MAURYA (25CS60R57)

## NAME : SHIVAM RANA (25CS60R76)

# Threaded Secure Chat Server with Authentication, Rooms, Redis, and Publish--Subscribe

**Language:** Python 3.9+\
**Course:** Internet Architecture and Protocols (CS60008)\
**Assignment:** Assignment--1

------------------------------------------------------------------------

# 1. Introduction

This project implements a **secure multi-client chat system** using
**TCP sockets and threading in Python**.

The system demonstrates several important concepts from **Internet
Architecture and Distributed Systems**, including:

-   Blocking I/O networking
-   Thread-based concurrency
-   Secure authentication
-   Session management
-   Duplicate login handling
-   Chat rooms
-   Publish--Subscribe communication model
-   Distributed shared state using Redis
-   TLS encryption
-   Containerized deployment using Docker

The final system supports **multiple chat server instances connected
through Redis**, enabling **scalable real-time messaging**.

------------------------------------------------------------------------

# 2. Technologies Used

## Programming Language

-   Python 3.9+

## Python Libraries

-   socket
-   threading
-   time
-   json
-   os
-   ssl

## External Libraries

-   bcrypt -- password hashing
-   redis -- Redis client library

## Infrastructure

-   Redis (in-memory datastore)
-   Docker
-   Docker Compose

------------------------------------------------------------------------

# 3. Project Structure

    IAP-ASSIGNMENT_1/
    │
    ├── client/
    │   └── client.py
    │
    ├── server/
    │   ├── server.py
    │   ├── users.json
    │   ├── cert.pem
    │   └── key.pem
    │
    ├── docker-compose.yml
    ├── Dockerfile
    │
    └── README.md

------------------------------------------------------------------------

# 4. System Architecture

    Clients
       │
       │ TLS encrypted connection
       ▼
    Chat Server (Thread-per-client)
       │
       │ Redis client
       ▼
    Redis Server
     ├ Room membership
     ├ User session mapping
     └ Pub/Sub messaging

Multiple chat servers can run simultaneously while sharing state via
Redis.

------------------------------------------------------------------------

# 5. How to Run the Project

## Step 1 -- Build Containers

    docker-compose build

## Step 2 -- Start System

    sudo docker-compose down
    sudo docker-compose up --build

Expected output:

    redis_1       | Ready to accept connections
    chatserver_1  | Secure chat server started

## Step 3 -- Connect Client

    openssl s_client -connect localhost:9000

------------------------------------------------------------------------

# 6. Client--Server Protocol

After connection the server sends:

    [SERVER] LOGIN <username> <password>

Example:

    LOGIN SM 12345

If authentication succeeds:

    Login successful

------------------------------------------------------------------------

# 7. Supported Commands

  Command                                         Description
  ----------------------------------------------- ----------------------------
  LOGIN `<username>`{=html} `<password>`{=html}   Authenticate user
  /join `<room>`{=html}                           Join a chat room
  /rooms                                          List available rooms
  /subscribe `<user>`{=html}                      Subscribe to a publisher
  /unsubscribe `<user>`{=html}                    Remove subscription
  /subs                                           List current subscriptions

Messages sent without `/` are treated as chat messages.

------------------------------------------------------------------------

# 8. Problem-1: Thread-Based Chat Server

The server uses a **thread-per-client model**.

    Client connects
         ↓
    Server accepts connection
         ↓
    New thread created
         ↓
    Thread handles client communication

This allows multiple clients to interact concurrently.

------------------------------------------------------------------------

# 9. Problem-2: Authentication

User credentials are stored in:

    users.json

Passwords are hashed using **bcrypt**.

Example hash:

    $2b$12$Fhsjdhsjdhjsd...

Authentication process:

    client password
          ↓
    bcrypt.checkpw()
          ↓
    hash comparison

------------------------------------------------------------------------

# 10. Problem-3: Duplicate Login Handling

Policy implemented:

**Force Logout Existing Session**

If the same user logs in again:

    Existing session → terminated
    New session → accepted

------------------------------------------------------------------------

# 11. Problem-4: Chat Rooms

Users can join rooms using:

    /join <room>

Example:

    /join sports

Rooms are stored in Redis sets:

    room:lobby
    room:sports

------------------------------------------------------------------------

# 12. Problem-5: Publish--Subscribe Model

Users subscribe to publishers:

    /subscribe <username>

Example:

    /subscribe SM

Messages are delivered only to subscribed users.

------------------------------------------------------------------------

# 13. Problem-6: Redis Integration

Redis provides distributed shared state.

## Room Membership

    SADD room:lobby SM
    SADD room:lobby SR

## User--Room Mapping

    HSET user_rooms SM lobby

## Cross-Server Messaging

Servers publish messages:

    r.publish("chat", message)

Other servers receive them using Redis Pub/Sub.

------------------------------------------------------------------------

# 14. Problem-7: TLS Security

TLS is implemented using Python's ssl module.

Server loads certificate:

    context.load_cert_chain("cert.pem", "key.pem")

Verify secure connection:

    openssl s_client -connect localhost:9000

Example output:

    TLSv1.3
    Cipher TLS_AES_256_GCM_SHA384

------------------------------------------------------------------------

# 15. Problem-8: Docker Deployment

Containers used:

    chatserver
    redis

Start system:

    docker-compose up --build

Docker automatically builds the image and runs Redis and chat server
containers.

------------------------------------------------------------------------

# 16. Thread Safety

Shared data structures are protected using:

    threading.Lock()

This prevents race conditions when multiple threads access shared
resources.

------------------------------------------------------------------------

# 17. Conclusion

This project demonstrates a **secure distributed chat server
architecture** using:

-   Threaded TCP networking
-   Authentication with bcrypt
-   Chat rooms
-   Publish--Subscribe messaging
-   Redis distributed state
-   TLS encrypted communication
-   Docker container deployment

The implementation provides a scalable foundation for real‑world
messaging systems.
