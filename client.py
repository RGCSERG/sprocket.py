import socket
import base64
import hashlib

# Define the WebSocket server URL (replace with your server's URL)
websocket_url = "localhost"
websocket_port = 1000

# WebSocket key and GUID
websocket_key = "your_websocket_key"
websocket_guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


# Function to perform the WebSocket handshake
def perform_websocket_handshake(client_socket):
    request = (
        f"GET /websocket HTTP/1.1\r\n"
        f"Host: {websocket_url}:{websocket_port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {websocket_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )

    client_socket.send(request.encode("utf-8"))

    response = client_socket.recv(4096).decode("utf-8")
    if "101 Switching Protocols" in response:
        return True
    else:
        return False


# Create a WebSocket client
def start_websocket_client(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    print(f"Connected to {host}:{port}")

    if perform_websocket_handshake(client_socket):
        print("WebSocket handshake successful")

        # Implement your WebSocket logic here
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received data: {data.decode('utf-8')}")
    else:
        print("WebSocket handshake failed")

    client_socket.close()


if __name__ == "__main__":
    start_websocket_client(websocket_url, websocket_port)
