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
from typing import Any, Callable, Final, List, NoReturn, Optional, Tuple, Type


__all__: Final[List[str]] = ["ServerSocket"]


class ServerSocket(ABC):
    """
    Class for a WebSocket server implementation that handles WebSocket connections, messages and HTTP requests.
    """

    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        """
        Args:
            HOST str: The hostname or IP address to which the server socket should bind.
            PORT int: The port number for incoming connections.
            BUFFER_SIZE int: Buffer size for reading data from sockets.
            WS_ENDPOINT str: The WebSocket endpoint to handle.
            MAX_FRAME_SIZE int: Maximum WebSocket frame size.
            TIMEOUT int: Timeout value for socket operations.
            BACKLOG int: Number of unaccepted connections allowed before refusing new connections.

        _Args:
            _WEBSOCKET_GUID str: Set to 258EAFA5-E914-47DA-95CA-C5AB0DC85B11 - The specific GUID for websocket servers as defined in RFC6455.
            _LOCK threading.Lock: Threading lock for synchronising access to shared resources.
            _server_socket socket: Main server socket for incoming connections.
            _rooms dict: Data structure for managing WebSocket rooms or groups.
            _event_handlers dict: Event handlers for WebSocket events.
            _active_sockets list: List of all open socket connections.
            _websocket_sockets list: List of WebSocket connections currently managed.
            _request_handler HTTPRequestHandler: Class for handling HTTP requests.
            _frame_decoder WebsocketFrame: Class for decoding WebSocket frames.
            _frame_encoder WebSocketFrameEncoder: Class for encoding any given payload into WebSocket frame(s).
        """

    @abstractmethod
    def _remove_socket_from_lists(self, socket: socket) -> None:
        """
        Removes any given socket from all active socket lists,
        so that the socket is no longer read from.
        """

    @abstractmethod
    def _send_websocket_message(
        self,
        socket: socket,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Sends a WebSocket message to a specific client,
        identified by the provided socket argument.

        This method is typically used to send control frames.

        Args:
            socket socket: The client socket to send the message to.
            message Optional[str]: The message to send to the client.
            opcode Optional[bytes]: The WebSocket frame opcode.
        """

    @abstractmethod
    def _close_socket(self, socket: socket) -> None:
        """
        Closes a client socket and cleans up any associated resources.

        Args:
            client_socket socket: The client socket to be closed.
        """

    @abstractmethod
    def _setup_socket(self) -> None:
        """
        Sets up the server socket for accepting client connections.
        """

    @abstractmethod
    def _create_sec_accept_key(self, sec_websocket_key: str) -> bytes:
        """
        Creates the 'Sec-WebSocket-Accept' header value for a WebSocket handshake.
        This is done by taking the base64 encoded sha1 hash of the concatenation of the Sec-WebSocket-Key nonce,
        and the GUID str (ignoring all leading and trailing whitespace).

        Args:
            sec_websocket_key str: The 'Sec-WebSocket-Key' from the client's request.

        Returns:
            encoded_key bytes: The 'Sec-WebSocket-Accept' value.
        """

    @abstractmethod
    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """
        Triggers all handlers linked to the given event,
        passing in any given positional / keyword argument(s) to the function.

        Args:
            event str: The name of the event to be triggered.
            *args tuple: Takes in all positional arguments and adds them to a tuple.
            **kwargs dict[str, Any]: Takes in all key word values and assigns the value to a keyword in a dictionary.
        """

    @abstractmethod
    def _trigger_event_from_message(self, final_message: dict) -> None:
        """
        Takes the final WebSocket message converts it to a dictionary and takes the keyword value
        (the event name) and triggers the given event.

        All WebSocket messages received from a valid client should be dictionaries.

        Args:
            final_message str: The final decoded message received from a client.
        """

    @abstractmethod
    def _handle_handshake(self, socket: socket, headers: dict) -> None:
        """
        Handles a WebSocket handshake request from a client, and establishes WebSocket connections.

        Args:
            socket socket: The client socket with the WebSocket handshake request.
            headers dict: The headers from the WebSocket handshake request.
        """

    # @abstractmethod
    # def _read_recv(self, socket: socket) -> Any | None:
    #     """
    #     Reads data from a client socket, by waiting for incoming messages,
    #     and retrying if errors occur.

    #     Args:
    #         socket socket: The client socket for data to be read from.

    #     Returns:
    #         data bytes: The data read from the socket,
    #         or None.
    #     """

    @abstractmethod
    def _receive_http_request(self, socket: socket) -> str:
        """
        Reads an incoming HTTP request from a client,
        and decodes + constructs it to form a full HTTP request.

        Args:
            socket socket: The client socket from which the HTTP request is coming from.

        Returns:
            decoded_request_data str: The full HTTP request in str format.
        """

    @abstractmethod
    def _handle_request(self, socket: socket) -> None:
        """
        The main handler method for any given HTTP request, utilises the _receive_http_request method,
        and the instance of the _request_handler.

        Args:
            socket socket: The client socket sending the request.
        """

    @abstractmethod
    def _pong(self, socket: socket) -> None:
        """
        Sends a pong frame to a client socket.

        Args:
            socket socket: The client socket for the pong frame to be sent to.
        """

    @abstractmethod
    def _check_control_frame(self, opcode: bytes, socket: socket) -> None:
        """
        Inspects a WebSocket frame's opcode to identify control frames and handles them accordingly.

        Args:
            opcode bytes: The opcode of the WebSocket frame.
            socket socket: The client socket that sent the frame.
        """

    @abstractmethod
    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        """
        Determines whether a WebSocket frame is the final frame of a message.

        Args:
            frame_in_bytes bytes: The WebSocket frame data.

        Returns:
            bool: True if it's the final frame, otherwise False.
        """

    @abstractmethod
    def _handle_message(self, socket: socket) -> None:
        """
        Processes and handles incoming WebSocket messages received from a client socket.

        Args:
            socket socket: The client socket with the WebSocket messages.
        """

    @abstractmethod
    def _create_new_client_thread(self, client_socket: socket) -> None:
        """
        Creats a new thread to handle communications with a specific client.

        Args:
            client_socket socket: The client socket to be handled.
        """

    @abstractmethod
    def _handle_connection(self) -> None:
        """
        Used for accepting and handling new client connections to the server.
        """

    @abstractmethod
    def _listen_for_messages(self) -> None:
        """
        Used for managing the main loop which handles incoming client connections
        and their messages.
        """

    @abstractmethod
    def start(self) -> None:
        """
        Starts the WebSocket server and listens for incoming connections on the specified host and port,
        using the _listen_for_messages method as the main listening thread.
        """

    @abstractmethod
    def leave_room(self, socket: socket, room_name: Optional[str] = "") -> None:
        """
        Removes a client (identified by their socket) from a specified chat room,
        if no room is provided the client socket is removed from all its active rooms.

        Args:
            socket socket: The client socket to be removed from the chat room.
            room_name str: The name of the chat room to leave.
        """

    @abstractmethod
    def stop(self):
        """
        Shuts down the server socket, without forcing clients to close connection.
        """

    @abstractmethod
    def join_room(self, room_name: str, socket: socket) -> None:
        """
        Adds a client (identified by their socket) to a specified chat room, creating the room if it doesn't exist.

        Args:
            socket socket: The client socket to be added to the chat room.
            room_name str: The name of the chat room to join.
        """

    @abstractmethod
    def emit(
        self, event: str, socket: socket, payload: (str | bytes | dict | None) = ""
    ) -> None:
        """
        Emits a message to any given client socket,
        converting the event and payload into a keyword:value dictionary.

        Args:
            event str: The given event for the WebSocket message to be sent across.
            socket socket: The client socket to which the message is to be sent too.
            payload (str | bytes | dict | None): The payload to be sent with the event.
        """

    @abstractmethod
    def broadcast_message(
        self, event: Optional[str] = "", payload: (str | bytes | dict | None) = ""
    ) -> None:
        """
        Broadcasts a message to all WebSocket clients currently connected to the server.

        Args:
            payload Optional[str]: The message to broadcast to clients.
        """

    @abstractmethod
    def ping(self, socket: socket) -> None:
        """
        Sends a WebSocket Ping frame to a specific client, prompting a Pong response.

        Args:
            socket socket: The client socket to send the Ping frame to.
        """

    @abstractmethod
    def on(self, event: str, handler: Callable) -> None:
        """
        Registers any given custom event handler,  to a specific event.

        Args:
            event str: The event to listen for.
            handler Callable: The function to be executed when the event occurs.
        """

    @abstractmethod
    def to(
        self, room_name: str
    ) -> Type["RoomEmitter"]:  # Type is used here to avoid undefined errors.
        """
        Emits a message to a specific room, returning an instance of the RoomEmitter class,
        (defined below).

        Args:
            room_name str: The specific room to be emitted to.

        Returns:
            RoomEmitter: Returns an instance of the room emitter class.
        """


class RoomEmitter(ABC):
    """
    Allows for messages to be emitted to a particular room,
    not just all or one client.
    """
