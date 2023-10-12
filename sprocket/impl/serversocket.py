"""Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import base64
import hashlib
import random
import select
import socket
from typing import Final, List, Optional
from .websocketbase import WebSocketBaseImpl

DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
content="text/html;charset=utf-8">\r\n
<TITLE>200 OK</TITLE></HEAD><BODY>\r\n
<H1>200 OK</H1>\r\n
Welcome to the default.\r\n
</BODY></HTML>\r\n\r\n"""

__all__: Final[List[str]] = ["ServerSocketImpl"]


class ServerSocketImpl(WebSocketBaseImpl):
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
    ) -> None:
        super().__init__(TCP_HOST, TCP_PORT, TCP_BUFFER_SIZE, WS_ENDPOINT)

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

        print(f"Received message: {message}")

        (method, target, http_version, headers_map) = self._parse_request(message)

        print("method, target, http_version: ", method, target, http_version)
        print(f"headers: {headers_map}")

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
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {sec_websocket_accept_value.decode()}\r\n"
            "\r\n"
        )

        print("\nresponse:\n", response)

        client_socket.send(response.encode("utf-8"))

    def _generate_sec_websocket_accept(self, sec_websocket_key):
        # We generate the accept key by concatenating the sec-websocket-key
        # and the GUID, Sha1 hashing it, and base64 encoding it.
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
