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

import socket
from abc import ABC, abstractmethod
from typing import Any, Final, List, NoReturn, Optional, Tuple


__all__: Final[List[str]] = ["ServerSocket"]


class ServerSocket(ABC):
    def __init__(
        self,
        TCP_HOST: Optional[str],
        TCP_PORT: Optional[int],
        TCP_BUFFER_SIZE: Optional[int],
        WS_ENDPOINT: Optional[str],
        MAX_FRAME_SIZE: Optional[int],
        TIMEOUT: Optional[int],
        DEFAULT_HTTP_RESPONSE: Optional[bytes],
        WEBSOCKET_GUID: Optional[str],
        BACKLOG: Optional[int],
    ) -> None:
        """
        Abstract base class for a WebSocket server implementation that handles WebSocket connections and HTTP requests.

        Attributes:
            TCP_HOST str: The hostname or IP address to which the server socket should bind.
            TCP_PORT int: The port number for incoming connections.
            TCP_BUFFER_SIZE int: Buffer size for reading data from TCP sockets.
            WS_ENDPOINT str: The WebSocket endpoint to handle.
            MAX_FRAME_SIZE int: Maximum WebSocket frame size.
            TIMEOUT int: Timeout value for socket operations.
            DEFAULT_HTTP_RESPONSE bytes: Default HTTP response for regular HTTP requests.
            WEBSOCKET_GUID str: Unique identifier for WebSocket connections.
            BACKLOG int: Number of unaccepted connections allowed before refusing new connections.
            _server_socket socket: Main server socket for incoming connections.
            _event_handlers dict: Event handlers for WebSocket events.
            _rooms dict: Data structure for managing WebSocket rooms or groups.
            _input_sockets list: List of all open socket connections.
            _ws_sockets list: List of WebSocket connections currently managed.
            _frame_decoder WebsocketFrame: Instance for decoding WebSocket frames.
            _frame_encoder WebSocketFrameEncoder: Instance for encoding payloads into WebSocket frames.
            _control_frame_types ControlFrame: Instance for WebSocket control frame types.
            _LOCK threading.Lock: Threading lock for synchronizing access to shared resources.

            Subclasses should provide implementations for the abstract methods to create a functional WebSocket system.
        """
        pass

    @abstractmethod
    def _setup_socket(self) -> None:
        """
        Set up the server socket for accepting client connections.
        This method should handle creating and binding the server socket.
        """
        pass

    @abstractmethod
    def _generate_random_websocket_guid(self) -> str:
        """
        Generate a random WebSocket GUID.
        This method should generate and return a random WebSocket GUID.
        """
        pass

    @abstractmethod
    def _listen_for_messages(self) -> NoReturn:
        """
        Listen for incoming messages from clients and handle them.
        This method should manage the main loop for handling incoming client connections
        and their messages.
        """
        pass

    @abstractmethod
    def _handle_new_connection(self) -> None:
        """
        Handle a new incoming client connection.
        This method should be responsible for accepting and handling new client connections.
        """
        pass

    @abstractmethod
    def _create_new_client_thread(self, client_socket: socket) -> None:
        """
        Create a new thread to handle a client's connection.
        This method should create a new thread to handle the communication with a specific client.

        Args:
            client_socket socket: The client socket to be handled.
        """
        pass

    @abstractmethod
    def _handle_request(self, client_socket: socket) -> None:
        """
        Handle an incoming HTTP request from a client.
        This method should parse and process incoming HTTP requests from clients.

        Args:
            client_socket socket: The client socket containing the HTTP request.
        """
        pass

    @abstractmethod
    def _handle_ws_handshake_request(
        self, client_socket: socket, headers_map: dict
    ) -> None:
        """
        Handle a WebSocket handshake request from a client.
        This method should handle WebSocket handshake requests and establish WebSocket connections.

        Args:
            client_socket socket: The client socket with the WebSocket handshake request.
            headers_map dict: The headers from the WebSocket handshake request.
        """
        pass

    @abstractmethod
    def _generate_sec_websocket_accept(self, sec_websocket_key: str) -> bytes:
        """
        Generate the 'Sec-WebSocket-Accept' value for a WebSocket handshake.
        This method should generate and return the value for the 'Sec-WebSocket-Accept' header.

        Args:
            sec_websocket_key str: The 'Sec-WebSocket-Key' from the client's request.

        Returns:
            bytes: The 'Sec-WebSocket-Accept' value.
        """
        pass

    @abstractmethod
    def _is_valid_ws_handshake_request(
        self, method: str, target: str, http_version: str, headers_map: dict
    ) -> bool:
        """
        Check if an HTTP request is a valid WebSocket handshake request.
        This method should determine if an incoming HTTP request is a valid WebSocket handshake request.

        Args:
            method str: The HTTP method.
            target str: The request target.
            http_version str: The HTTP version.
            headers_map dict: The headers from the request.

        Returns:
            bool: True if the request is a valid WebSocket handshake request, False otherwise.
        """
        pass

    @abstractmethod
    def _parse_request(self, request: str) -> Tuple[str, str, str, dict]:
        """
        Parse an incoming HTTP request.
        This method should parse and extract information from an incoming HTTP request.

        Args:
            request str: The HTTP request as a string.

        Returns:
            Tuple[str, str, str, dict]: A tuple containing the HTTP method, request target,
            HTTP version, and a dictionary of headers.
        """
        pass

    @abstractmethod
    def _check_control_frame(self, opcode: bytes, client_socket: socket) -> None:
        """
        Check if a WebSocket frame is a control frame and handle it.
        This method should inspect a WebSocket frame's opcode to identify control frames and handle them accordingly.

        Args:
            opcode bytes: The opcode of the WebSocket frame.
            client_socket socket: The client socket that sent the frame.
        """
        pass

    @abstractmethod
    def _pong(self, client_socket: socket) -> None:
        """
        Send a WebSocket Pong frame to a client.
        This method should send a WebSocket Pong frame to acknowledge a Ping frame from the client.

        Args:
            client_socket socket: The client socket to send the Pong frame to.
        """
        pass

    @abstractmethod
    def _trigger(self, event: str, *args: Tuple, **kwargs: dict[str, Any]) -> None:
        """
        Trigger event handlers for a specific event.
        This method should trigger event handlers associated with a particular event.

        Args:
            event str: The event to trigger.
            args Tuple: Additional arguments to pass to the event handlers.
            kwargs dict: Additional keyword arguments to pass to the event handlers.
        """
        pass

    @abstractmethod
    def _handle_websocket_message(self, client_socket: socket) -> None:
        """
        Handle incoming WebSocket messages from a client.
        This method should process and handle incoming WebSocket messages received from a client.

        Args:
            client_socket socket: The client socket with the WebSocket messages.
        """
        pass

    @abstractmethod
    def _trigger_message_event(self, message: str, client_socket: socket) -> None:
        """
        Trigger an event for an incoming WebSocket message.
        This method should trigger a specific event for an incoming WebSocket message.

        Args:
            message (str): The WebSocket message received.
            client_socket socket: The client socket that sent the message.
        """
        pass

    @abstractmethod
    def _is_final_frame(self, data_in_bytes: bytes) -> bool:
        """
        Check if a WebSocket frame is the final frame of a message.
        This method should determine whether a WebSocket frame is the final frame of a message.

        Args:
            data_in_bytes bytes: The WebSocket frame data.

        Returns:
            bool: True if it's the final frame, False otherwise.
        """
        pass

    @abstractmethod
    def _read_recv(self, client_socket: socket) -> bytes:
        """
        Read data from the client socket.
        This method should read data from the client socket, waiting for incoming messages.

        Args:
            client_socket socket: The client socket to read data from.

        Returns:
            bytes: The data read from the socket.
        """
        pass

    @abstractmethod
    def _close_socket(self, client_socket: socket) -> None:
        """
        Close a client socket.
        This method should close a client socket and clean up any associated resources.

        Args:
            client_socket socket: The client socket to close.
        """
        pass
