# server.py
import socket
import threading
import string
import random
import time

KEEP_ALIVE_TIMEOUT = 30

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.lock = threading.Lock()
        self.connected_users = {}  # client_socket: {ip, port, room, last_seen}
        self.chat_rooms = {}  # room_name: ChatRoom

    def broadcast_user_list(self):
        while True:
            print()
            with self.lock:
                now = time.time()
                for client, data in list(self.connected_users.items()):
                    print(now - data["last_seen"])
                    if now - data["last_seen"] > KEEP_ALIVE_TIMEOUT:
                        print("Client disconnected.")
                        try:
                            client.close()
                        except:
                            pass
                        del self.connected_users[client]
                        continue

                    if data["room"]:
                        print(data["name"])
                        peers = [
                            f"{info['ip']}:{info['listening_port']}:{info['name']}"
                            for c, info in self.connected_users.items()
                            if info["room"] == data["room"] and c != client
                        ]
                    else:
                        print("not in room")
                        print(data["name"])
                        peers = [
                            f"{info['ip']}:{info['listening_port']}:{info['name']}"
                            for c, info in self.connected_users.items()
                            if info["room"] is None and c != client
                        ]

                    try:
                        client.send(f"USER_LIST {';'.join(peers)}".encode('utf-8'))
                    except:
                        del self.connected_users[client]

            time.sleep(5)

    def handle_client(self, client_socket):
        initialized = False
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode('utf-8').strip()
                print(message)
                if message.startswith("INIT "):
                    print("Client initialized")
                    initialized = True
                    _, listening_port, name = message.split(" ", 2)
                    client_ip, client_port = client_socket.getpeername()
                    with self.lock:
                        existing_names = [user_info["name"] for user_info in self.connected_users.values()]
                        if name in existing_names:
                            client_socket.send(f"INIT_INCOMPLETE".encode('utf-8'))
                            initialized = False
                            break
                        self.connected_users[client_socket] = {
                            "ip": client_ip,
                            "port": client_port,
                            "listening_port": listening_port,
                            "room": None,
                            "last_seen": time.time(),
                            "name": name
                        }
                    client_socket.send(f"INIT_COMPLETE".encode('utf-8'))
                elif message == "KEEP_ALIVE":
                    if initialized:
                        with self.lock:
                            self.connected_users[client_socket]["last_seen"] = time.time()

                elif message.startswith("create_room "):
                    if initialized:
                        _, room_name = message.split(" ", 1)
                        with self.lock:
                            if room_name in self.chat_rooms:
                                client_socket.send(f"[ChatRooms] Room '{room_name}' already exists.".encode('utf-8'))
                            else:
                                new_room = ChatRoom(room_name)
                                self.chat_rooms[room_name] = new_room
                                client_socket.send(f"[ChatRooms] Room '{room_name}' created. Room key: {new_room.return_room_key()}".encode('utf-8'))

                elif message.startswith("join_room "):
                    if initialized:
                        _, room_key = message.split(" ", 1)
                        with self.lock:
                            matched_room = None

                            for room in self.chat_rooms.values():
                                if room.return_room_key() == room_key:
                                    matched_room = room
                                    break

                            if matched_room:
                                matched_room.current_users.append(client_socket)
                                self.connected_users[client_socket]["room"] = matched_room.name
                                client_socket.send(f"[ChatRooms] Joined room '{matched_room.name}'".encode('utf-8'))
                            else:
                                client_socket.send(f"ERROR: No room found with key '{room_key}'".encode('utf-8'))
                elif message == "leave_room":
                    if initialized:
                        with self.lock:

                            current_room = self.connected_users[client_socket]["room"]
                            print(current_room)
                            if current_room:
                                # Remove user from current room
                                if client_socket in self.chat_rooms[current_room].current_users:
                                    self.chat_rooms[current_room].current_users.remove(client_socket)
                                self.connected_users[client_socket]["room"] = None
                                client_socket.send(f"[ChatRooms] Left room '{current_room}'".encode('utf-8'))

                                # Optional: delete room if now empty
                                if not self.chat_rooms[current_room].current_users:
                                    del self.chat_rooms[current_room]
                                    print(f"[ChatRooms] Deleted empty room '{current_room}'")
                            else:
                                client_socket.send("ERROR: You are not in a room.".encode('utf-8'))

                else:
                    client_socket.send(message)

            except:
                break

        with self.lock:
            if client_socket in self.connected_users:
                del self.connected_users[client_socket]
        client_socket.close()

    def broadcast_message(self, message, sender_socket):
        with self.lock:
            sender_info = self.connected_users.get(sender_socket, {})
            sender_room = sender_info.get("room")

            for client, info in self.connected_users.items():
                if client != sender_socket:
                    if info["room"] == sender_room:
                        try:
                            client.send(message)
                        except:
                            pass

    def run(self):
        print(f"Server is running on {self.host}:{self.port}")
        threading.Thread(target=self.broadcast_user_list, daemon=True).start()

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()


class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.room_key = self.generate_room_key()
        self.current_users = []

    def generate_room_key(self, length=16):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    def return_room_key(self):
        return self.room_key


if __name__ == "__main__":
    server = Server("0.0.0.0", 12345)
    server.run()
