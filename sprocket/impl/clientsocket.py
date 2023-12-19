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


import threading, json
from typing import Callable, Final, List, Optional
from loguru import logger

from .clientsocketbase import *

__all__: Final[List[str]] = ["ClientSocket"]


class ClientSocket(ClientSocketBaseImpl):  #  comments + sort layout
    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        TIMEOUT: Optional[int] = 5,
        MAX_FRAME_SIZE: Optional[int] = 125,
    ) -> None:
        super().__init__(
            HOST=HOST,
            PORT=PORT,
            BUFFER_SIZE=BUFFER_SIZE,
            TIMEOUT=TIMEOUT,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
        )

    def start(self) -> None:
        try:
            self._client_socket.connect(
                (self._HOST, self._PORT)
            )  # Connect the Client Socket to the server.

            logger.success(
                f"Connected to {self._HOST}:{self._PORT}"
            )  # Log a successful connection.

            if self._perform_websocket_handshake():  # Perform a WebSocket handshake.
                logger.success(
                    "WebSocket handshake successful"
                )  # Log a successfull handshake.

                self._socket_open = True  # Set the socket to open.

                listen_thread = threading.Thread(
                    target=self._listen_for_messages
                )  # Open a listening thread.
                listen_thread.start()  # Start the listening thread.

            else:
                logger.warning(
                    "WebSocket handshake failed"
                )  # Log an unsuccessful handshake.

        except ConnectionRefusedError:  # Catch a connection error.
            logger.warning("Connection to server actively refused")  # Log the error.

        return

    def close(self) -> None:
        logger.warning("Sending Close Frame")

        if self._socket_open:  # If the socket is not already closed.
            self._send_websocket_message(
                opcode=self._frame_types.close
            )  # Send a close frame.

        return

    def ping(self) -> None:
        if self._socket_open:  # if the socket is open.
            logger.debug("Activating Ping")

            self._send_websocket_message(
                opcode=self.control_frame_types.ping
            )  # Send a ping frame to the client socket.

        return

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:  # If event not found.
            self._event_handlers[
                event
            ] = []  # Append it to the _event_handlers dictionary.
        self._event_handlers[event].append(
            handler
        )  # Then append the provided handler to the dictionary entry.

        return

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        json_data: dict = {event: payload}  # Set up the json_data.

        payload: str = json.dumps(json_data)  # Dump the json_data into str format.

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload
        )  # Encode the payload into WebSocket frames.

        for frame in frames:  # For each frame created.
            self._client_socket.send(frame)  # Send it to the server.

        return
