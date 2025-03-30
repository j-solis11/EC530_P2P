import socket
import threading

# Server class to handle client connections
class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = []

    def broadcast(self, message, client_socket):
        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(message)
                except:
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024)
                if message:
                    self.broadcast(message, client_socket)
                else:
                    break
            except:
                break
        self.clients.remove(client_socket)
        client_socket.close()

    def run(self):
        print("Server is running and waiting for connections.")
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address}.")
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

server = ChatServer("localhost", 12345)
server.run()
