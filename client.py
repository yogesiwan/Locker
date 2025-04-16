import socket
import threading
import sys

class ChatClient:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        """Connect to the server"""
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            
            # Send username to the server
            self.client_socket.send(self.username.encode('utf-8'))
            
            # Start threads for sending and receiving messages
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            send_thread = threading.Thread(target=self.send_messages)
            send_thread.daemon = True
            send_thread.start()
            
            # Keep the main thread alive
            send_thread.join()
            
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client_socket.close()
            
    def receive_messages(self):
        """Receive and display messages from the server"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    print("Disconnected from server")
                    self.client_socket.close()
                    break
                print(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.client_socket.close()
                break
                
    def send_messages(self):
        """Send messages to the server"""
        try:
            print("Type your messages (press Enter to send, Ctrl+C to exit):")
            while True:
                message = input()
                self.client_socket.send(message.encode('utf-8'))
                
        except KeyboardInterrupt:
            print("\nDisconnecting from server...")
        except Exception as e:
            print(f"Error sending message: {e}")
        finally:
            self.client_socket.close()
            sys.exit(0)
            

if __name__ == "__main__":
    # Get server details and username
    if len(sys.argv) < 4:
        print("Usage: python client.py <server_ip> <server_port> <username>")
        print("Example: python client.py 127.0.0.1 9999 Alice")
        sys.exit(1)
        
    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    
    # Create and start client
    client = ChatClient(host, port, username)
    client.connect() 