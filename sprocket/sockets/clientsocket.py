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
from typing import Any, Callable, Final, List, Optional


__all__: Final[List[str]] = ["ClientSocket"]


class ClientSocket(ABC):
    """
    Class for a WebSocket client implementation that handles WebSocket handshakes and messages.
    """

    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
    ) -> None:
        """
        Args:
            HOST str: The hostname or IP address to which the client socket should connect to.
            PORT int: The port number for outgoing handshakes.
            BUFFER_SIZE int: Buffer size for reading data from socket.
            WS_ENDPOINT str: The WebSocket endpoint to connect to.
            MAX_FRAME_SIZE int: Maximum WebSocket frame size.
            TIMEOUT int: Timeout value for socket operations.

        _Args:
            _WEBSOCKET_KEY str: Randomly generated Sec-WebSocket-Key nonce.
            _LOCK threading.Lock: Threading lock for synchronising access to shared resources.
            _client_socket socket: Main client socket for WebSocket communication.
            _event_handlers dict: Event handlers for WebSocket events.
            _response_handler HTTPResponseHandler: Class for handling HTTP responses.
            _frame_decoder WebsocketFrame: Class for decoding WebSocket frames.
            _frame_encoder WebSocketFrameEncoder: Class for encoding any given payload into WebSocket frame(s).
        """

    @abstractmethod
    def _generate_random_websocket_key() -> str:
        """
        Generates a random valid Sec-WebSocket-Key nonce, conforming to RFC6455 requirements.


        Returns:
            base64_random_key str: Returns uft-8 version of base_64 encoded 16 bytes sequence.
        """

    @abstractmethod
    def _setup_socket(self) -> None:
        """
        Sets up the client socket for WebSocket communication.
        """

    @abstractmethod
    def _close_socket(self) -> None:
        """
        Sends a close frame to the server, and closes the client socket.
        """

    @abstractmethod
    def _send_websocket_message(
        self,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Sends a WebSocket message to the server, usually used to send control frames.


        Args:
            message Optional[str]: The message to send to the client.
            opcode Optional[bytes]: The WebSocket frame opcode.
        """

    @abstractmethod
    def _ping(self) -> None:
        """
        Sends a Ping frame to the server, prompting a pong response.
        """

    @abstractmethod
    def _pong(self) -> None:
        """
        Sends a pong frame to the server.
        """

    @abstractmethod
    def _check_control_frame(self, opcode: bytes, socket: socket) -> None:
        """
        Inspects a WebSocket frame's opcode to identify control frames and handles them accordingly.

        Args:
            opcode bytes: The opcode of the WebSocket frame.
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
    def _perform_websocket_handshake(self, retry_count: Optional[int] = 0) -> bool:
        """
        Performs a valid WebSocket handshake, using recursion to avoid connection errors,
        returning false for a failed connection and true for a successful connection.

        Args:
            retry_count Optional[int]: Not to be passed in when used outside of the function,
            used to idenitfy how many attempts have been made.
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
    def _handle_message(self) -> None:
        """
        Processes and handles incoming WebSocket messages received from a the server.
        """

    @abstractmethod
    def _listen_for_messages(self) -> None:
        """
        Used for managing the main loop which handles incoming messages from the server.
        """

    @abstractmethod
    def start(self) -> None:
        """
        Establishes a WebSocket connection with the server, by performing the WebSocket handshake,
        and starts listening for messages.
        """

    @abstractmethod
    def close(self) -> None:
        """
        Closes the WebSocket connection by sending a close frame to the server.
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
    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        """
        Emits a message to the server,
        converting the event and payload into a keyword:value dictionary.

        Args:
            event str: The given event for the WebSocket message to be sent across.
            payload (str | bytes | dict | None): The payload to be sent with the event.
        """
