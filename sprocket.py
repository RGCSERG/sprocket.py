import time
from sprocket import ServerSocketImpl


server = ServerSocketImpl()


def deal_with_stuff(args, kwargs):
    server.join_room(args, kwargs)


def send(args, kwargs):
    server.broadcast_to_room(message=args, client_socket=kwargs)


server.on("join_room", deal_with_stuff)
server.on("send_message", send)

if __name__ == "__main__":
    server.start()


# import base64
# import hashlib
# import select
# import socket

# # Define WebSocket GUID as per the WebSocket specification
# websocket_guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
# content="text/html;charset=utf-8">\r\n
# <TITLE>200 OK</TITLE></HEAD><BODY>\r\n
# <H1>200 OK</H1>\r\n
# Welcome to the default.\r\n
# </BODY></HTML>\r\n\r\n"""


# # Function to perform the WebSocket handshake
# def perform_websocket_handshake(client_socket):
#     data = client_socket.recv(1024).decode("utf-8")
#     headers = data.split("\r\n")
#     websocket_key = None

#     # Parse the WebSocket key from the headers
#     for header in headers:
#         if "Sec-WebSocket-Key" in header:
#             websocket_key = header.split(": ")[1]

#     if websocket_key:
#         # Perform the WebSocket handshake
#         response_key = base64.b64encode(
#             hashlib.sha1((websocket_key + websocket_guid).encode("utf-8")).digest()
#         ).decode("utf-8")
#         response = (
#             "HTTP/1.1 101 Switching Protocols\r\n"
#             "Upgrade: websocket\r\n"
#             "Connection: Upgrade\r\n"
#             f"Sec-WebSocket-Accept: {response_key}\r\n"
#             "\r\n"
#         )

#         print("\nresponse:\n", response)

#         client_socket.send(response.encode("utf-8"))
#         return True
#     else:
#         return False


# def is_valid_ws_handshake_request(method, target, http_version, headers_map):
#     is_get = method == "GET"

#     http_version_number = float(http_version.split("/")[1])
#     http_version_enough = http_version_number >= 1.1

#     headers_valid = (
#         ("upgrade" in headers_map and headers_map.get("upgrade") == "websocket")
#         and ("connection" in headers_map and headers_map.get("connection") == "Upgrade")
#         and ("sec-websocket-key" in headers_map)
#     )
#     return is_get and http_version_enough and headers_valid


# # WebSocket Frame Processing (WebsocketFrame class)
# # See https://datatracker.ietf.org/doc/html/rfc6455#section-5.2
# class WebsocketFrame:
#     """A simple representation of a websocket frame"""

#     _fin = 0
#     _rsv1 = 0
#     _rsv2 = 0
#     _rsv3 = 0
#     _opcode = 0
#     _payload_length = 0
#     _payload_data = b""

#     def populateFromWebsocketFrameMessage(self, data_in_bytes):
#         self._parse_flags(data_in_bytes)
#         self._parse_payload_length(data_in_bytes)
#         self._maybe_parse_masking_key(data_in_bytes)
#         self._parse_payload(data_in_bytes)

#     def _parse_flags(self, data_in_bytes):
#         first_byte = data_in_bytes[0]
#         # Bad python formatting, but it helps to see where each one is.
#         self._fin = first_byte & 0b10000000
#         self._rsv1 = first_byte & 0b01000000
#         self._rsv2 = first_byte & 0b00100000
#         self._rsv3 = first_byte & 0b00010000
#         self._opcode = first_byte & 0b00001111

#         second_byte = data_in_bytes[1]
#         self._mask = second_byte & 0b10000000

#     def _parse_payload_length(self, data_in_bytes):
#         # The payload length is the first 7 bits of the 2nd byte, or more if
#         # it's longer.
#         payload_length = (data_in_bytes[1]) & 0b01111111
#         # We can also parse the mask key at the same time. If the payload
#         # length is <126, the mask will start at the 3th byte.
#         mask_key_start = 2
#         # Depending on the payload length, the masking key may be offset by
#         # some number of bytes. We can assume big endian for now because I'm
#         # just running it locally.
#         if payload_length == 126:
#             # If the length is 126, then the length also includes the next 2
#             # bytes. Also parse length into first length byte to get rid of
#             # mask bit.
#             payload_length = int.from_bytes(
#                 (bytes(payload_length) + data_in_bytes[2:4]), byteorder="big"
#             )
#             # This will also mean the mask is offset by 2 additional bytes.
#             mask_key_start = 4
#         elif payload_length == 127:
#             # If the length is 127, then the length also includes the next 8
#             # bytes. Also parse length into first length byte to get rid of
#             # mask bit.
#             payload_length = int.from_bytes(
#                 (bytes(payload_length) + data_in_bytes[2:9]), byteorder="big"
#             )
#             # This will also mean the mask is offset by 8 additional bytes.
#             mask_key_start = 10
#         self._payload_length = payload_length
#         self._mask_key_start = mask_key_start

#     def _maybe_parse_masking_key(self, data_in_bytes):
#         if not self._mask:
#             return
#         self._masking_key = data_in_bytes[
#             self._mask_key_start : self._mask_key_start + 4
#         ]

#     def _parse_payload(self, data_in_bytes):
#         # All client data_in_bytess should be masked
#         payload_data = b""
#         if self._payload_length == 0:
#             return payload_data
#         if self._mask:
#             # Get the masking key
#             payload_start = self._mask_key_start + 4
#             encoded_payload = data_in_bytes[payload_start:]
#             # To decode the payload, we do a bitwise OR with the mask at the
#             # mask index determined by the payload index modulo 4.
#             decoded_payload = [
#                 byte ^ self._masking_key[i % 4]
#                 for i, byte in enumerate(encoded_payload)
#             ]
#             payload_data = bytes(decoded_payload)
#         else:
#             # If we don't have a mask, the payload starts where the mask would
#             # have.
#             payload_start = self._mask_key_start
#             payload_data = data_in_bytes[payload_start:]
#         self._payload_data = payload_data

#     def get_payload_data(self):
#         return self._payload_data


# # Create a WebSocket server
# def start_websocket_server(host, port):
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     server_socket.bind((host, port))
#     server_socket.listen(5)

#     input_sockets = [server_socket]

#     print(f"WebSocket server listening on {host}:{port}")

#     while True:
#         readable_sockets = select.select(input_sockets, [], [], 5)[0]
#         for socket in readable_sockets:
#             if socket.fileno() == -1:
#                 continue
#             if socket == server_socket:
#                 print("handling connection")
#                 handle_new_connection(server_socket, input_sockets)


# def handle_new_connection(server_socket, input_sockets):
#     client_socket, client_address = server_socket.accept()
#     print(f"Accepted connection from {client_address}")

#     if perform_websocket_handshake(client_socket):
#         # Handle WebSocket communication
#         while True:
#             data = client_socket.recv(1024)
#             if not data:
#                 break

#             # WebSocket Frame Processing
#             websocket_frame = WebsocketFrame()
#             websocket_frame.populateFromWebsocketFrameMessage(data)

#             # Payload Data Processing
#             payload_data = websocket_frame.get_payload_data()
#             print(f"Received data: {payload_data.decode('utf-8')}")


# if __name__ == "__main__":
#     host = "localhost"
#     port = 5000
#     start_websocket_server(host, port)


# from class_testing import ServerSocketImpl

# server = ServerSocketImpl()

# if __name__ == "__main__":
#     server.start()
