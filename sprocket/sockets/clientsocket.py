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

from abc import ABC, abstractmethod
import socket
from typing import Any, Final, List, Optional


__all__: Final[List[str]] = ["ClientSocket"]


class ClientSocket(ABC):
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        TCP_KEY: Optional[str] = None,
        TIMEOUT: Optional[int] = 5,
        MAX_FRAME_SIZE: Optional[int] = 125,
    ) -> None:
        """
        Client socket Class.

        Parameters:
        - TCP_HOST str: The host to connect to.
        - TCP_PORT int: The port to connect to.
        - TCP_BUFFER_SIZE int: The buffer size for data transmission.
        - TCP_KEY str: The WebSocket key used for the connection.
        - TIMEOUT int: The timeout duration for socket operations.
        - MAX_FRAME_SIZE int: Maximum frame size for WebSocket frames.

        Subclasses should provide implementations for the abstract methods to create a functional WebSocket system.
        """

    @abstractmethod
    def _setup_socket(self) -> None:
        """
        Method for setting up the WebSocket socket connection.
        """
        pass

    @abstractmethod
    def _check_control_frame(self, opcode: bytes, client_socket: socket) -> None:
        """
        Method for handling control frames in WebSocket communication.

        Args:
            opcode bytes: The opcode of the WebSocket frame.
            client_socket socket: The client socket that sent the frame.
        """
        pass

    @abstractmethod
    def _pong(self, client_socket: socket) -> None:
        """
        Method for sending a Pong response in WebSocket communication.

        Args:
            client_socket socket: The client socket to send the Pong frame from.
        """
        pass

    @abstractmethod
    def _handle_websocket_message(self, client_socket: socket) -> None:
        """
        Method for handling WebSocket messages.

        Args:
            client_socket socket: The client socket with the WebSocket messages.
        """
        pass

    @abstractmethod
    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """
        Method for triggering event handlers in WebSocket communication.

        Args:
            event str: The event to trigger.
            args Tuple: Additional arguments to pass to the event handlers.
            kwargs dict: Additional keyword arguments to pass to the event handlers.
        """
        pass

    @abstractmethod
    def _listen_for_messages(self) -> None:
        """
        Method for listening to incoming WebSocket messages.
        """
        pass
