# Python TCP Chat Application

A simple TCP-based group chat application that allows multiple users to connect and chat together.

## Features

- Server listens on all interfaces (0.0.0.0)
- Multiple clients can connect simultaneously
- Messages from one client are broadcast to all other clients
- Server announces when users join or leave the chat
- Connect using netcat or telnet (no need to download any files)

## Requirements

- Python 3.6 or higher (server only)
- Netcat (nc) or telnet (for clients)

## Usage

### Starting the Server

Run the server script on the computer that will act as the host:

```
python server.py
```

The server will start listening on 0.0.0.0:9999 by default.

### Connect via Command Line Client (Option 1)

To connect to the server using the Python client:

```
python client.py <server_ip> <server_port> <username>
```

Example:
```
python client.py 192.168.1.5 9999 Alice
```

- `<server_ip>`: The IP address of the server (use the public IP if connecting over the internet)
- `<server_port>`: The port number (default: 9999)
- `<username>`: Your chosen username in the chat

### Connect via Netcat or Telnet (Option 2 - No Download Required)

Your friends can simply use netcat (nc) or telnet to connect without downloading any files:

#### For Windows users:
```
telnet <server_ip> 9999
```
Then enter their username when prompted.

#### For macOS/Linux users:
```
nc <server_ip> 9999
```
Then enter their username when prompted.

### Using the Chat

Once connected:
1. Type your message and press Enter to send it to all connected clients
2. To exit, close the terminal window or press Ctrl+C

## Important Notes for Internet Usage

- If you want to use this over the internet, you'll need to:
  - Configure your router to forward port 9999 to the computer running the chat server
  - Use your public IP address for clients to connect
  - Consider using SSL/TLS for secure communication (not implemented in this basic version)

## Customization

You can modify the server.py file to change the default host and port:

```python
server = ChatServer(host='0.0.0.0', port=9999)
``` #   L o c k e r  
 