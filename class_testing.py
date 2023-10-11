import base64
import hashlib
import random
import select
import socket
from typing import Optional


DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
content="text/html;charset=utf-8">\r\n
<TITLE>200 OK</TITLE></HEAD><BODY>\r\n
<H1>200 OK</H1>\r\n
Welcome to the default.\r\n
</BODY></HTML>\r\n\r\n"""


def generate_random_websocket_guid():
    # Characters that can be used in the GUID
    characters = "0123456789ABCDEF"

    # Generate a random 32-character string
    random_guid = "".join(random.choice(characters) for _ in range(32))

    # Format it as a WebSocket GUID
    formatted_guid = "-".join(
        [
            random_guid[:8],
            random_guid[8:12],
            random_guid[12:16],
            random_guid[16:20],
            random_guid[20:],
        ]
    )

    return formatted_guid


class WebsocketFrame:
    def __init__(self):
        self._fin = 0
        self._rsv1 = 0
        self._rsv2 = 0
        self._rsv3 = 0
        self._opcode = 0
        self._mask = 0
        self._payload_length = 0
        self._mask_key = None
        self._payload_data = b""

    def populateFromWebsocketFrameMessage(self, data_in_bytes):
        self._parse_flags(data_in_bytes)
        self._parse_payload_length(data_in_bytes)
        self._maybe_parse_masking_key(data_in_bytes)
        self._parse_payload(data_in_bytes)

    def _parse_flags(self, data_in_bytes):
        first_byte = data_in_bytes[0]
        self._fin = (first_byte & 0b10000000) >> 7
        self._rsv1 = (first_byte & 0b01000000) >> 6
        self._rsv2 = (first_byte & 0b00100000) >> 5
        self._rsv3 = (first_byte & 0b00010000) >> 4
        self._opcode = first_byte & 0b00001111

        second_byte = data_in_bytes[1]
        self._mask = (second_byte & 0b10000000) >> 7

    def _parse_payload_length(self, data_in_bytes):
        payload_length = data_in_bytes[1] & 0b01111111
        mask_key_start = 2

        if payload_length == 126:
            payload_length = int.from_bytes(data_in_bytes[2:4], byteorder="big")
            mask_key_start = 4
        elif payload_length == 127:
            payload_length = int.from_bytes(data_in_bytes[2:10], byteorder="big")
            mask_key_start = 10

        self._payload_length = payload_length
        self._mask_key_start = mask_key_start

    def _maybe_parse_masking_key(self, data_in_bytes):
        if self._mask:
            self._mask_key = data_in_bytes[
                self._mask_key_start : self._mask_key_start + 4
            ]

    def _parse_payload(self, data_in_bytes):
        payload_data = b""
        if self._payload_length > 0:
            payload_start = (
                self._mask_key_start if self._mask else self._mask_key_start - 4
            )
            encoded_payload = data_in_bytes[
                payload_start : payload_start + self._payload_length
            ]

            if self._mask:
                decoded_payload = [
                    byte ^ self._mask_key[i % 4]
                    for i, byte in enumerate(encoded_payload)
                ]
                payload_data = bytes(decoded_payload)
            else:
                payload_data = encoded_payload

        self._payload_data = payload_data

    def get_payload_data(self):
        return self._payload_data


from typing import Optional
import random


class ServerSocketImpl(WebsocketFrame):
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        DEFAULT_HTTP_RESPONSE: Optional[bytes] = DEFAULT_HTTP_RESPONSE,
        WEBSOCKET_GUID: Optional[str] = None,
        BACKLOG: Optional[int] = 5,
        TIMEOUT: Optional[int] = 5,
    ):
        super().__init__()

        self.TCP_HOST = TCP_HOST

        if TCP_PORT is not None and not (1 <= TCP_PORT <= 65535):
            raise ValueError("TCP_PORT must be in the range of 1-65535.")
        self.TCP_PORT = TCP_PORT

        self.TCP_BUFFER_SIZE = TCP_BUFFER_SIZE
        self.WS_ENDPOINT = WS_ENDPOINT

        if WEBSOCKET_GUID is not None:
            self.WEBSOCKET_GUID = WEBSOCKET_GUID
        else:
            # Generate a random WebSocket GUID for each instance
            self.WEBSOCKET_GUID = self._generate_random_websocket_guid()

        self.DEFAULT_HTTP_RESPONSE = DEFAULT_HTTP_RESPONSE
        self.BACKLOG = BACKLOG
        self.TIMEOUT = TIMEOUT
        self.input_sockets = []
        self.ws_sockets = []

        self._setup_socket()

    def _setup_socket(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.TCP_HOST, self.TCP_PORT))

        self.input_sockets.append(self.tcp_socket)

    def _generate_random_websocket_guid(self) -> str:
        # Characters that can be used in the GUID
        characters = "0123456789ABCDEF"

        # Generate a random 32-character string
        random_guid = "".join(random.choice(characters) for _ in range(32))

        # Format it as a WebSocket GUID
        formatted_guid = "-".join(
            [
                random_guid[:8],
                random_guid[8:12],
                random_guid[12:16],
                random_guid[16:20],
                random_guid[20:],
            ]
        )

        return formatted_guid

    def start(self):
        self.tcp_socket.listen(self.BACKLOG)
        print("Listening on port: ", self.TCP_PORT)

        while True:
            # Get the sockets that are ready to read (the first of the
            # three-tuple).
            readable_sockets = select.select(self.input_sockets, [], [], self.TIMEOUT)[
                0
            ]

            for socket in readable_sockets:
                # Make sure it's not already closed
                if socket.fileno() == -1:
                    continue
                if socket == self.tcp_socket:
                    print("Handling main door socket")
                    self._handle_new_connection()
                elif socket in self.ws_sockets:
                    print("Handling websocket message")
                    self._handle_websocket_message(socket)
                else:
                    print("Handling regular socket read")
                    self._handle_request(socket)

    def _handle_new_connection(self):
        # When we get a connection on the main socket, we want to accept a new
        # connection and add it to our input socket list. When we loop back around,
        # that socket will be ready to read from.
        client_socket, client_addr = self.tcp_socket.accept()
        print("New socket", client_socket.fileno(), "from address:", client_addr)
        self.input_sockets.append(client_socket)

    def _handle_websocket_message(self, client_socket):
        # Let's assume that we get a full single frame in each recv (may not
        # be true IRL)
        data_in_bytes = client_socket.recv(self.TCP_BUFFER_SIZE)

        self.populateFromWebsocketFrameMessage(data_in_bytes)

        print("Received message:", self.get_payload_data().decode("utf-8"))
        return

    def _handle_request(self, client_socket):
        print("Handling request from client socket:", client_socket.fileno())
        message = ""
        # Very naive approach: read until we find the last blank line
        while True:
            data_in_bytes = client_socket.recv(self.TCP_BUFFER_SIZE)
            # Connnection on client side has closed.
            if len(data_in_bytes) == 0:
                self._close_socket(client_socket)
                return
            message_segment = data_in_bytes.decode()
            message += message_segment
            if len(message) > 4 and message_segment[-4:] == "\r\n\r\n":
                break

        print("Received message:")
        print(message)

        (method, target, http_version, headers_map) = self._parse_request(message)

        print("method, target, http_version:", method, target, http_version)
        print("headers:")
        print(headers_map)

        # We will know it's a websockets request if the handshake request is
        # present.
        if target == self.WS_ENDPOINT:
            print("request to ws endpoint!")
            if self._is_valid_ws_handshake_request(
                method, target, http_version, headers_map
            ):
                self._handle_ws_handshake_request(client_socket, headers_map)
                return
            else:
                # Invalid WS request.
                client_socket.send(b"HTTP/1.1 400 Bad Request")
                self._close_socket(client_socket)
                return

        # For now, just return a 200. Should probably return length too, eh
        client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + DEFAULT_HTTP_RESPONSE)
        self._close_socket(client_socket)

    def _handle_ws_handshake_request(self, client_socket, headers_map):
        self.ws_sockets.append(client_socket)

        # To handle a WS handshake, we have to generate an accept key from the
        # sec-websocket-key and a magic string.
        sec_websocket_accept_value = self._generate_sec_websocket_accept(
            headers_map.get("sec-websocket-key")
        )

        # We can now build the response, telling the client we're switching
        # protocols while providing the key.
        websocket_response = ""
        websocket_response += "HTTP/1.1 101 Switching Protocols\r\n"
        websocket_response += "Upgrade: websocket\r\n"
        websocket_response += "Connection: Upgrade\r\n"
        websocket_response += (
            "Sec-WebSocket-Accept: " + sec_websocket_accept_value.decode() + "\r\n"
        )
        websocket_response += "\r\n"

        print("\nresponse:\n", websocket_response)

        client_socket.send(websocket_response.encode())

    def _generate_sec_websocket_accept(self, sec_websocket_key):
        # We generate the accept key by concatenating the sec-websocket-key
        # and the magic string, Sha1 hashing it, and base64 encoding it.
        # See https://datatracker.ietf.org/doc/html/rfc6455#page-7
        combined = sec_websocket_key + self.WEBSOCKET_GUID
        hashed_combined_string = hashlib.sha1(combined.encode())
        encoded = base64.b64encode(hashed_combined_string.digest())
        return encoded

    def _is_valid_ws_handshake_request(self, method, target, http_version, headers_map):
        # There are a few things to verify to see if it's a valid WS handshake.
        # First, the method must be get.
        is_get = method == "GET"
        # HTTP version must be >= 1.1. We can do a really naive check.
        http_version_number = float(http_version.split("/")[1])
        http_version_enough = http_version_number >= 1.1
        # Finally, we should have the right headers. This is a subset of what we'd
        # really want to check.
        headers_valid = (
            ("upgrade" in headers_map and headers_map.get("upgrade") == "websocket")
            and (
                "connection" in headers_map
                and headers_map.get("connection") == "Upgrade"
            )
            and ("sec-websocket-key" in headers_map)
        )
        return is_get and http_version_enough and headers_valid

    # Parses the first line and headers from the request.
    def _parse_request(self, request):
        headers_map = {}
        # Assume headers and body are split by '\r\n\r\n' and we always have them.
        # Also assume all headers end with'\r\n'.
        # Also assume it starts with the method.
        split_request = request.split("\r\n\r\n")[0].split("\r\n")
        [method, target, http_version] = split_request[0].split(" ")
        headers = split_request[1:]
        for header_entry in headers:
            [header_name, value] = header_entry.split(": ")
            # Headers are case insensitive, so we can just keep track in lowercase.
            # Here's a trick though: the case of the values matter. Otherwise,
            # things don't hash and encode right!
            headers_map[header_name.lower()] = value
        return (method, target, http_version, headers_map)

    def _close_socket(self, client_socket):
        print("closing socket")
        if client_socket in self.ws_sockets:
            self.ws_sockets.remove(client_socket)
        self.input_sockets.remove(client_socket)
        client_socket.close()
        return


# class WebsocketMessageBuilder(WebsocketFrame):
#     def __init__(self):
#         super().__init__()

#     def build_message(self, data):
#         # Automatically determine the opcode based on the data type
#         if isinstance(data, str):
#             self._opcode = 0x01  # Text frame opcode
#             data = data.encode("utf-8")
#         elif isinstance(data, bytes):
#             self._opcode = 0x02  # Binary frame opcode
#         elif isinstance(data, dict):
#             self._opcode = 0x01  # Text frame opcode for JSON data
#             data = self._json_dumps(data)
#             data = data.encode("utf-8")
#         else:
#             raise ValueError("Unsupported data type")

#         # Automatically determine if fragmentation is needed based on data size
#         if len(data) <= 125:
#             # Data can fit in a single frame
#             self.create_final_frame(data, opcode=self._opcode)
#         else:
#             # Data should be fragmented
#             self.create_fragmented_frame(data, opcode=self._opcode)

#         return self.to_bytes()

#     def build_fragmented_message(self, data, is_final=False, opcode=None):
#         if opcode is not None:
#             self._opcode = opcode

#         self.create_fragmented_frame(data, opcode=self._opcode)
#         if is_final:
#             self._fin = 1
#         return self.to_bytes()

#     def _json_dumps(self, json_data):
#         json_text = "{"

#         for key, value in json_data.items():
#             # Handle key and value as strings
#             key_str = f'"{key}"'
#             if isinstance(value, str):
#                 value_str = f'"{value}"'
#             else:
#                 value_str = str(value)

#             # Append key-value pair to JSON text
#             json_text += f"{key_str}: {value_str}, "

#         # Remove the trailing comma and space, if present
#         if len(json_data) > 0:
#             json_text = json_text[:-2]

#         json_text += "}"

#         return json_text
