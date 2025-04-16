import socket
import threading
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

# Store active client connections
clients = {}

class ChatConnection:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.messages = []
        
    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.client_socket.send(self.username.encode('utf-8'))
            self.connected = True
            
            # Start a thread to receive messages
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Error connecting: {e}")
            return False
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    self.connected = False
                    break
                self.messages.append(message)
            except:
                self.connected = False
                break
    
    def send_message(self, message):
        if self.connected:
            try:
                self.client_socket.send(message.encode('utf-8'))
                return True
            except:
                self.connected = False
                return False
        return False
    
    def get_messages(self):
        messages = self.messages.copy()
        self.messages = []
        return messages
    
    def disconnect(self):
        self.connected = False
        self.client_socket.close()

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    username = data.get('username')
    server_ip = data.get('server_ip')
    server_port = int(data.get('server_port', 9999))
    
    # Create a unique client ID
    client_id = f"{username}_{len(clients)}"
    
    # Create a new chat connection
    client = ChatConnection(server_ip, server_port, username)
    if client.connect():
        clients[client_id] = client
        return jsonify({"success": True, "client_id": client_id})
    else:
        return jsonify({"success": False, "error": "Failed to connect to server"})

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    client_id = data.get('client_id')
    message = data.get('message')
    
    if client_id in clients:
        if clients[client_id].send_message(message):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to send message"})
    else:
        return jsonify({"success": False, "error": "Client not found"})

@app.route('/messages', methods=['GET'])
def messages():
    client_id = request.args.get('client_id')
    
    if client_id in clients:
        return jsonify({"messages": clients[client_id].get_messages()})
    else:
        return jsonify({"messages": []})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.json
    client_id = data.get('client_id')
    
    if client_id in clients:
        clients[client_id].disconnect()
        del clients[client_id]
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Client not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 