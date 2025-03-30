import socket
import threading

class ChatClient:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                print(f"New message: {message}")
            except:
                print("Connection lost!")
                break

    def send_message(self):
        while True:
            message = input(f"{self.username}: ")
            self.client_socket.send(f"{self.username}: {message}".encode('utf-8'))

    def run(self):
        print(f"{self.username} has joined the chat!")
        threading.Thread(target=self.receive_messages).start()
        self.send_message()

username = input("Enter your username: ")
client = ChatClient("localhost", 12345, username)
client.run()
