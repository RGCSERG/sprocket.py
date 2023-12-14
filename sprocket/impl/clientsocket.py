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


import random, threading, json
from typing import Callable, Final, List, Optional
from loguru import logger

from .clientsocketbase import *

__all__: Final[List[str]] = ["ClientSocketImpl"]


class ClientSocketImpl(ClientSocketBaseImpl):  #  comments + sort layout
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

        self.ID = random.randint(
            1000000, 9999999
        )  # maybe implement some decent id system

    def start(self) -> None:
        try:
            self._client_socket.connect((self._HOST, self._PORT))

            logger.debug(f"Connected to {self._HOST}:{self._PORT}")

            if self._perform_websocket_handshake():
                logger.success("WebSocket handshake successful")

                self._socket_open = True
                listen_thread = threading.Thread(target=self._listen_for_messages)
                listen_thread.start()

            else:
                logger.warning("WebSocket handshake failed")
        except ConnectionRefusedError:
            logger.warning("Connection to server actively refused")

    def close(self) -> None:
        logger.warning("Sending Close Frame")
        if self._socket_open:
            self._send_websocket_message(opcode=self._frame_types.close)

    def ping(self) -> None:
        """
        Send a Ping frame to the server.
        """
        if self._socket_open:
            logger.debug("Activating Ping")
            self._send_websocket_message(opcode=self._frame_types.ping)

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        json_data: dict = {event: payload}

        payload: str = json.dumps(json_data)

        frames = self._frame_encoder.encode_payload_to_frames(payload=payload)

        for frame in frames:
            self._client_socket.send(frame)
