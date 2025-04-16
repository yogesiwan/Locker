import socket
import threading
import time
import re

class ChatServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {client_socket: username}
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        
        try:
            self.accept_connections()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.server_socket.close()
            
    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address}")
            
            # Start a new thread to handle this client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
            
    def clean_input(self, text):
        """Clean input from telnet/netcat clients"""
        if not text:
            return ""
            
        # Process ANSI escape sequences and control characters
        # Common patterns: 
        # - Backspace: \b or ^H
        # - Arrow keys and other controls: escape sequences like \x1b[A, \x1b[B, etc.
        
        # Remove ANSI escape sequences (including arrow keys, colors, etc.)
        text = re.sub(r'\x1b\[[\x30-\x3F]*[\x20-\x2F]*[\x40-\x7E]', '', text)
        
        # Process backspaces (\b or ^H)
        while '\b' in text or '\x08' in text:
            text = re.sub('.\x08', '', text)
            text = re.sub('.\b', '', text)
        
        # Remove any remaining control characters
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        
        return text.strip()
    
    def get_online_users_text(self):
        """Get formatted text of online users"""
        if not self.clients:
            return "No one else is online."
            
        users = list(self.clients.values())
        
        if len(users) == 1:
            return f"{users[0]} is online."
        elif len(users) == 2:
            return f"{users[0]} and {users[1]} are online."
        else:
            return f"{', '.join(users[:-1])}, and {users[-1]} are online."
    
    def handle_client(self, client_socket, client_address):
        try:
            # Configure socket with longer timeout
            client_socket.settimeout(300.0)  # 5 minute timeout
            
            # Send welcome message with proper line endings for all clients
            welcome_msg = "\r\n=== Welcome to the Developer's Locker Room ===\r\n"
            welcome_msg += "Please enter your username: "
            client_socket.sendall(welcome_msg.encode('utf-8'))
            
            # Get username (handle it specially with extra care)
            username_bytes = bytearray()
            while True:
                chunk = client_socket.recv(1)
                if not chunk:
                    print(f"Connection closed during username input from {client_address}")
                    return
                
                # Check for line endings
                if chunk == b'\n' or chunk == b'\r':
                    if username_bytes:  # If we have collected some bytes, break
                        break
                    continue  # Skip empty line feeds
                
                username_bytes.extend(chunk)
                
                # Avoid infinite loop if too much data without line ending
                if len(username_bytes) > 50:
                    break
            
            # Convert username bytes to string and clean it
            try:
                username = username_bytes.decode('utf-8', errors='ignore')
                username = self.clean_input(username)
            except Exception as e:
                print(f"Error decoding username: {e}")
                username = f"Guest{len(self.clients)}"
            
            # Handle empty username
            if not username:
                username = f"Guest{len(self.clients)}"
                
            print(f"User '{username}' joined from {client_address}")
            
            # Add client to our dictionary (need to do this before getting online users)
            self.clients[client_socket] = username
            
            # Create a list of online users for the welcome message
            # Get online users except the current user
            online_users = []
            for sock, name in self.clients.items():
                if sock != client_socket:
                    online_users.append(name)
            
            # Format the online users message
            if not online_users:
                online_msg = "No one else is online."
            elif len(online_users) == 1:
                online_msg = f"{online_users[0]} is online."
            else:
                online_msg = f"{', '.join(online_users[:-1])}, and {online_users[-1]} are online."
            
            # Clear the screen before displaying the welcome message
            clear_screen = "\033[2J\033[H"  # ANSI escape sequence to clear screen and move cursor to top-left
            client_socket.sendall(clear_screen.encode('utf-8'))
            
            # Send welcome message
            welcome_msg = f"=== Welcome {username}! ===\r\n"
            welcome_msg += f"{online_msg}\r\n"
            welcome_msg += "-------------------------------------------------------\r\n"
            welcome_msg += "Start typing messages...\r\n\r\n"
            client_socket.sendall(welcome_msg.encode('utf-8'))
            
            # Send chat UI guidance
            help_msg = "=== Chat Help ===\r\n"
            help_msg += "- Your messages: YOU> [message]\r\n"
            help_msg += "- Others' messages: [username]> [message]\r\n"
            help_msg += "- Type '/help' to see this message again\r\n"
            help_msg += "- Type '/users' to see who's online\r\n"
            help_msg += "- Type '/quit' to exit the chat\r\n"
            help_msg += "----------------------------\r\n\r\n"
            client_socket.sendall(help_msg.encode('utf-8'))
            
            # Send initial prompt (only once)
            client_socket.sendall("Type your message: ".encode('utf-8'))
            
            # Broadcast that a new user has joined
            self.broadcast(f"SERVER: {username} has joined the chat!", client_socket)
            
            # Main loop to receive messages from this client
            buffer = bytearray()
            while True:
                try:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        print(f"Connection closed by client {username} from {client_address}")
                        break
                    
                    buffer.extend(chunk)
                    
                    # Process complete messages in the buffer
                    lines, buffer = self.extract_lines(buffer)
                    for line in lines:
                        try:
                            message = line.decode('utf-8', errors='ignore')
                            message = self.clean_input(message)
                            
                            if not message:  # Skip empty messages
                                client_socket.sendall("Type your message: ".encode('utf-8'))
                                continue
                                
                            # Check for commands
                            if message.startswith('/'):
                                self.handle_command(message, client_socket, username)
                                client_socket.sendall("Type your message: ".encode('utf-8'))
                                continue
                            
                            # Echo the message back to the sender
                            client_socket.sendall(f"\r\nYOU> {message}\r\nType your message: ".encode('utf-8'))
                            
                            # Broadcast to others
                            print(f"Message from {username}: {message}")
                            self.broadcast(f"{username}> {message}", client_socket)
                        except Exception as e:
                            print(f"Error processing message: {e}")
                    
                except socket.timeout:
                    print(f"Connection timeout for {username} from {client_address}")
                    break
                except Exception as e:
                    print(f"Error receiving data from {username} ({client_address}): {e}")
                    break
                    
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Client disconnected
            if client_socket in self.clients:
                username = self.clients[client_socket]
                del self.clients[client_socket]
                client_socket.close()
                self.broadcast(f"SERVER: {username} has left the chat.", None)
                print(f"Connection from {client_address} closed")
    
    def handle_command(self, command, client_socket, username):
        """Handle special commands entered by users"""
        command = command.lower()
        
        if command == '/help':
            help_msg = "\r\n=== Chat Help ===\r\n"
            help_msg += "- Your messages: YOU> [message]\r\n"
            help_msg += "- Others' messages: [username]> [message]\r\n"
            help_msg += "- Type '/help' to see this message again\r\n"
            help_msg += "- Type '/users' to see who's online\r\n"
            help_msg += "- Type '/quit' to exit the chat\r\n"
            help_msg += "----------------------------\r\n"
            client_socket.sendall(help_msg.encode('utf-8'))
            
        elif command == '/users':
            user_list = "\r\n=== Users Online ===\r\n"
            for sock, name in self.clients.items():
                if sock == client_socket:
                    user_list += f"- {name} (YOU)\r\n"
                else:
                    user_list += f"- {name}\r\n"
            user_list += f"Total: {len(self.clients)} users\r\n"
            user_list += "-------------------\r\n"
            client_socket.sendall(user_list.encode('utf-8'))
            
        elif command == '/quit':
            client_socket.sendall("\r\nGoodbye! Disconnecting...\r\n".encode('utf-8'))
            client_socket.close()
        
        # Could add more commands here
    
    def extract_lines(self, buffer):
        """Extract complete lines from buffer and return remaining buffer"""
        lines = []
        remaining = buffer
        
        # Find all complete lines (ending with \r, \n, or \r\n)
        while True:
            cr_index = remaining.find(b'\r')
            lf_index = remaining.find(b'\n')
            
            if cr_index == -1 and lf_index == -1:
                # No more line endings found
                break
                
            if cr_index != -1 and (lf_index == -1 or cr_index < lf_index):
                # CR found first
                lines.append(remaining[:cr_index])
                if cr_index + 1 < len(remaining) and remaining[cr_index + 1] == ord('\n'):
                    # CRLF
                    remaining = remaining[cr_index + 2:]
                else:
                    # CR alone
                    remaining = remaining[cr_index + 1:]
            else:
                # LF found first
                lines.append(remaining[:lf_index])
                remaining = remaining[lf_index + 1:]
        
        return lines, remaining
            
    def broadcast(self, message, sender_socket):
        """Send message to all clients except the sender"""
        print(f"Broadcasting: {message}")
        disconnected_clients = []
        
        for client_socket in self.clients:
            if client_socket != sender_socket:
                try:
                    # We only want to send the message, not add a prompt immediately
                    # The client should still have their prompt from before
                    client_socket.sendall(f"\r\n{message}\r\nType your message: ".encode('utf-8'))
                except Exception as e:
                    print(f"Error sending to client {self.clients.get(client_socket, 'Unknown')}: {e}")
                    # If sending fails, the client is likely disconnected
                    disconnected_clients.append(client_socket)
        
        # Clean up any disconnected clients
        for client_socket in disconnected_clients:
            print(f"Removing disconnected client: {self.clients.get(client_socket, 'Unknown')}")
            if client_socket in self.clients:
                del self.clients[client_socket]
                client_socket.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start() 