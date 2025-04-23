import socket
import threading
import sys
import random
import time

# ------------------------------
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
MY_PORT = random.randint(15000, 20000)
# ------------------------------

USERNAME = input("Enter your name: ")
initialized = False
peers_list = {}
in_room = False
muted_users = set()

def start_p2p_listener(listen_port):
    global USERNAME
    global initialized
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('', listen_port))
    listener.listen(5)
    print(f"[P2P] Listening on port {listen_port}")

    def accept_peers():
        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_peer_connection, args=(conn, addr), daemon=True).start()

    threading.Thread(target=accept_peers, daemon=True).start()

def handle_peer_connection(conn, addr):
    global USERNAME
    global initialized

    ip, port = addr
    name = None

    # Find the name from peers_list by matching IP and port
    for peer_name, (peer_ip, peer_port) in peers_list.items():
        if peer_ip == ip and peer_port == port:
            name = peer_name
            break

    if name is None:
        name = f"{ip}:{port}"  # fallback if name not found

    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            msg_decoded = msg.decode()
            if name in muted_users and msg_decoded.startswith(f"{name}:"):
                continue  # Skip showing this message
            print(f"{msg.decode()}")
        except:
            break
    conn.close()

def send_keep_alive(sock):
    while True:
        time.sleep(10)
        try:
            sock.send(b"KEEP_ALIVE")
        except:
            break
        

def broadcast_to_peers(message):
    global USERNAME
    global initialized
    for name, (ip, port) in peers_list.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(message.encode('utf-8'))
            sock.close()
            print(f"[P2P] Me: {message}")
        except Exception as e:
            print(f"[P2P] Failed to send to {name} at {ip}:{port} — {e}")

def read_server_messages(sock):
    global USERNAME
    global initialized
    while True:
        try:
            message = sock.recv(2048).decode()
            if not message:
                break
            
            if (message == "INIT_COMPLETE"):
                initialized = True
            elif message.startswith("INIT_INCOMPLETE"):
                USERNAME = input("Duplicate detected. Enter your name: ")
            if initialized:
                if message.startswith("USER_LIST"):
                    peers = message[len("USER_LIST "):].split("|")

                    updated_peers = {}  # Temporary dict to store the new list

                    for peer in peers:
                        if not peer.strip():
                            continue
                        try:
                            ip, port, name = peer.split(":")
                            updated_peers[name] = (ip, int(port))
                        except ValueError:
                            print(f"[WARN] Skipping invalid peer entry: {peer}")

                    # Overwrite the global peers_list with the updated one
                    peers_list.clear()
                    peers_list.update(updated_peers)

                
                else:
                    print(f"server msg: {message}")
        except:
            break

def read_user_input(sock):
    global USERNAME
    global initialized
    global in_room
    while True:
        try:
            msg = input()
            if msg:

                if msg.startswith("msg"):
                    try:
                        _, target_name, message_text = msg.split(" ", 2)
                        if target_name not in peers_list:
                            print(f"[P2P] No peer named '{target_name}' found.")
                            return
                        ip, port = peers_list[target_name]
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.connect((ip, port))
                            sock.send(f"[P2P] Message from {target_name}: {message_text}".encode('utf-8'))
                            sock.close()
                            print(f"[P2P] Message sent to {target_name} ({ip}:{port})")
                        except Exception as e:
                            print(f"[P2P] Failed to send message to {target_name}: {e}")
                    except ValueError:
                        print("Invalid format. Use: msg <username> <message>")
                elif msg.startswith("create_room "):
                    if in_room:
                        print("ERROR: Cannot create room, must leave current one first.")
                        return
                    sock.send(msg.encode('utf-8'))

                elif msg.startswith("join_room "):
                    if in_room:
                        print("ERROR: Cannot join room, must leave current one first.")
                        return
                    in_room = True
                    sock.send(msg.encode('utf-8'))
                elif msg.startswith("leave_room"):
                    if not in_room:
                        print("ERROR: Cannot join room, not in one.")
                        return
                    in_room = False
                    sock.send(msg.encode('utf-8'))
                elif msg.startswith("USERS"):
                    print("[Server] Active users:")
                    for name in peers_list:
                        print(f" - {name}")
                if msg.startswith("mute "):
                    _, to_mute = msg.split(" ", 1)
                    muted_users.add(to_mute)
                    print(f"[INFO] Muted {to_mute}")
                    continue
                elif msg.startswith("unmute "):
                    _, to_unmute = msg.split(" ", 1)
                    muted_users.discard(to_unmute)
                    print(f"[INFO] Unmuted {to_unmute}")
                    continue
                elif msg == "muted":
                    print("[INFO] Muted users:")
                    for user in muted_users:
                        print(f" - {user}")
                    continue
                else:
                    broadcast_to_peers(msg)
                
        except:
            break

# Start P2P server
start_p2p_listener(MY_PORT)

# Connect to main server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((SERVER_IP, SERVER_PORT))
server.send(f"INIT {MY_PORT} {USERNAME}".encode('utf-8'))

# Start background threads
threading.Thread(target=send_keep_alive, args=(server,), daemon=True).start()
threading.Thread(target=read_server_messages, args=(server,), daemon=True).start()
threading.Thread(target=read_user_input, args=(server,), daemon=True).start()

# Keep the main thread alive
while True:
    time.sleep(1)
