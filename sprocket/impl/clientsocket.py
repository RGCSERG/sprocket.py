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
import threading
from typing import Callable, Final, List, Optional
from loguru import logger

from .clientsocketbase import *

__all__: Final[List[str]] = ["ClientSocketImpl"]


class ClientSocketImpl(ClientSocketBaseImpl):
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        TCP_KEY: Optional[str] = None,
        TIMEOUT: Optional[int] = 5,
        MAX_FRAME_SIZE: Optional[int] = 125,  # Add error checking
        IS_MASKED: Optional[bool] = True,
    ) -> None:
        super().__init__(
            TCP_HOST=TCP_HOST,
            TCP_PORT=TCP_PORT,
            TCP_BUFFER_SIZE=TCP_BUFFER_SIZE,
            TCP_KEY=TCP_KEY,
            TIMEOUT=TIMEOUT,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
            IS_MASKED=IS_MASKED,
        )

        self.ID = random.randint(1000000, 9999999)

    def start(self) -> None:
        """
        Establish a WebSocket connection with the server.
        This method performs the WebSocket handshake and starts listening for messages.
        """
        try:
            self._client_socket.connect((self._TCP_HOST, self._TCP_PORT))

            logger.debug(f"Connected to {self._TCP_HOST}:{self._TCP_PORT}")

            if self._perform_websocket_handshake():
                logger.success("WebSocket handshake successful")

                self._socket_open = True
                listen_thread = threading.Thread(target=self._listen_for_messages)
                listen_thread.start()

            else:
                logger.warning("WebSocket handshake failed")
        except ConnectionRefusedError:
            logger.warning("Connection to server actively refused")

    def send_websocket_message(
        self,
        message: Optional[str] = "",
        event: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Send a WebSocket message to the server.

        Args:
            message (str, optional): The message to send.
            event (str, optional): The event name associated with the message.
            opcode (bytes, optional): The opcode indicating the type of message.
        """
        if self._socket_open:
            logger.debug("Sending Message")

            if event != "":
                full_message = f"{event}:{message}"
                frames = self._frame_encoder.encode_payload_to_frames(
                    payload=full_message, opcode=opcode
                )
            else:
                frames = self._frame_encoder.encode_payload_to_frames(
                    payload=message, opcode=opcode
                )

            for frame in frames:
                self._client_socket.send(frame)

    def close(self) -> None:
        """
        Close the WebSocket connection by sending a close frame to the server.
        """
        logger.warning("Sending Close Frame")
        if self._socket_open:
            self.send_websocket_message(opcode=self._control_frame_types.close)

    def ping(self) -> None:
        """
        Send a Ping frame to the server.
        """
        if self._socket_open:
            logger.debug("Activating Ping")
            self.send_websocket_message(opcode=self._control_frame_types.ping)

    def on(self, event: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event.

        Args:
            event (str): The name of the event to register.
            handler (Callable): The event handler function.
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
