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

from abc import abstractmethod, ABC
import socket
from typing import Final, List, NoReturn


__all__: Final[List[str]] = ["ServerSocket"]


class ServerSocket(ABC):
    """WebSocket server implementation that handles WebSocket connections and HTTP requests.
    Provides methods for setting up the WebSocket server, handling new connections,
    processing WebSocket messages, and responding to HTTP requests.

    Attributes:

    TCP_HOST: The host to bind the WebSocket server to. It defaults to "localhost."
    TCP_PORT: The port on which the WebSocket server listens. It defaults to 1000.
    TCP_BUFFER_SIZE: The size of the TCP buffer for receiving data. It defaults to 8192.
    WS_ENDPOINT: The WebSocket endpoint to handle WebSocket connections. It defaults to "/websocket."
    DEFAULT_HTTP_RESPONSE: The default HTTP response content. It is set to an HTML response.
    WEBSOCKET_GUID: A WebSocket GUID used for WebSocket handshake. If not provided, a random GUID is generated.
    BACKLOG: The maximum number of queued connections. It defaults to 5.
    TIMEOUT: The timeout value for socket select operations. It defaults to 5."""

    @abstractmethod
    def _setup_socket(self) -> None:
        """Sets up the server socket and adds it to the list of input sockets for handling connections"""

    @abstractmethod
    def _generate_random_websocket_guid(self) -> str:
        """Generates a random WebSocket GUID"""

    @abstractmethod
    def start(self) -> NoReturn:
        """Starts the WebSocket server, listening for incoming connections and handling requests"""

    @abstractmethod
    def _handle_new_connection(self) -> None:
        """Handles a new client connection to the server and adds it to the list of input sockets"""

    @abstractmethod
    def _handle_websocket_message(self, client_socket: socket) -> None:
        """Handles WebSocket messages received from WebSocket clients"""

    @abstractmethod
    def _handle_request(self, client_socket: socket) -> None:
        """Handles HTTP requests received from clients and checks for WebSocket handshake requests"""

    @abstractmethod
    def _handle_ws_handshake_request(
        self, client_socket: socket, headers_map: dict
    ) -> None:
        """Handles the WebSocket handshake by generating a response and switching to the WebSocket protocol"""

    @abstractmethod
    def _generate_sec_websocket_accept(self, sec_websocket_key: any) -> bytes:
        """Generates a Sec-WebSocket-Accept key for the WebSocket handshake"""

    @abstractmethod
    def _is_valid_ws_handshake_request(
        self, method: any, target: any, http_version: any, headers_map: dict
    ) -> bool:
        """Checks if an incoming request is a valid WebSocket handshake request"""

    @abstractmethod
    def _parse_request(self, request: any) -> tuple[any, any, any, dict]:
        """Parses the HTTP request to extract method, target, HTTP version, and headers"""

    @abstractmethod
    def _close_socket(self, client_socket: socket) -> None:
        """Closes a client socket and removes it from the list of input sockets"""
