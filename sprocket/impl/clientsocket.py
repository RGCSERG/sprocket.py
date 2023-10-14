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

import random
import socket
import threading
from typing import Final, List, Optional
from loguru import logger

from .websocketbase import WebSocketBaseImpl

__all__: Final[List[str]] = ["ClientSocketImpl"]


class ClientSocketImpl(WebSocketBaseImpl):
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        TCP_KEY: Optional[str] = None,
    ) -> None:
        super().__init__(TCP_HOST, TCP_PORT, TCP_BUFFER_SIZE, WS_ENDPOINT)
        self.TCP_HOST = TCP_HOST

        if TCP_PORT is not None and not (1 <= TCP_PORT <= 65535):
            raise ValueError("TCP_PORT must be in the range of 1-65535.")
        self.TCP_PORT = TCP_PORT

        self.TCP_BUFFER_SIZE = TCP_BUFFER_SIZE
        self.WS_ENDPOINT = WS_ENDPOINT

        if TCP_KEY is not None:
            self.TCP_KEY = TCP_KEY
        else:
            # Generate a random WebSocket key for each instance
            self.TCP_KEY = self._generate_random_websocket_key()

        self._setup_socket()

    def _setup_socket(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _generate_random_websocket_key(self) -> str:
        # Characters that can be used in the GUID
        characters = "0123456789ABCDEF"

        # Generate a random 32-character string
        random_key = "".join(random.choice(characters) for _ in range(32))

        return random_key

    def _perform_websocket_handshake(self):
        request = (
            f"GET /websocket HTTP/1.1\r\n"
            f"Host: {self.TCP_HOST}:{self.TCP_PORT}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self.TCP_KEY}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )

        self.client_socket.send(request.encode("utf-8"))

        response = self.client_socket.recv(self.TCP_BUFFER_SIZE).decode("utf-8")
        if "101 Switching Protocols" in response:
            return True
        else:
            return False

    def start(self):
        self.client_socket.connect((self.TCP_HOST, self.TCP_PORT))

        logger.debug(f"Connected to {self.TCP_HOST}:{self.TCP_PORT}")

        if self._perform_websocket_handshake():
            logger.success("WebSocket handshake successful")

            self.SOCKET_OPEN = True
            self.listen_thread = threading.Thread(target=self._listen_for_messages)
            self.listen_thread.start()

        else:
            logger.warning("WebSocket handshake failed")

    def _listen_for_messages(self):
        while self.SOCKET_OPEN:
            self._handle_websocket_message(self.client_socket)

    def send_websocket_message(
        self,
        message: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ):
        frames = self.frame_encoder.encode_payload_to_frames(
            payload=message, opcode=opcode
        )

        for frame in frames:
            self.client_socket.send(frame)

    def close(self):
        if hasattr(self, "client_socket"):
            self.send_websocket_message(opcode=self.control_frame_types.close)

    def ping(self):
        if hasattr(self, "client_socket"):
            self.send_websocket_message(opcode=self.control_frame_types.ping)

    def _close_socket(self, client_socket: socket):
        if self.SOCKET_OPEN:
            logger.warning("closing socket")
            self.SOCKET_OPEN = False
            client_socket.close()
            return
