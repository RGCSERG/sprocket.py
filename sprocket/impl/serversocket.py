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

import socket, threading
from typing import Any, Callable, Final, List, Optional
from loguru import logger
from .serversocketbase import *

DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
content="text/html;charset=utf-8">\r\n
<TITLE>200 OK</TITLE></HEAD><BODY>\r\n
<H1>200 OK</H1>\r\n
Welcome to the default.\r\n
</BODY></HTML>\r\n\r\n"""

__all__: Final[List[str]] = ["ServerSocketImpl"]


class ServerSocketImpl(ServerSocketBaseImpl):
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,  # add error checking
        IS_MASKED: Optional[bool] = True,
        DEFAULT_HTTP_RESPONSE: Optional[bytes] = DEFAULT_HTTP_RESPONSE,
        WEBSOCKET_GUID: Optional[str] = None,
        BACKLOG: Optional[int] = 5,
        TIMEOUT: Optional[int] = 5,
    ) -> None:
        super().__init__(
            TCP_HOST=TCP_HOST,
            TCP_PORT=TCP_PORT,
            TCP_BUFFER_SIZE=TCP_BUFFER_SIZE,
            WS_ENDPOINT=WS_ENDPOINT,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
            IS_MASKED=IS_MASKED,
            TIMEOUT=TIMEOUT,
            DEFAULT_HTTP_RESPONSE=DEFAULT_HTTP_RESPONSE,
            WEBSOCKET_GUID=WEBSOCKET_GUID,
            BACKLOG=BACKLOG,
        )

    def start(self) -> None:
        self._server_socket.listen(self._BACKLOG)
        logger.debug(f"Listening on port: {self._TCP_PORT}")

        listen_thread = threading.Thread(target=self._listen_for_messages)
        listen_thread.start()

    def broadcast_message(self, message: Optional[str] = "") -> None:
        for client_socket in self._ws_sockets:
            try:
                frames = self._frame_encoder.encode_payload_to_frames(message)
                for frame in frames:
                    client_socket.send(frame)
            except Exception as e:
                # Handle any errors or disconnections here
                logger.warning(f"Error broadcasting message to client: {e}")

    def send_websocket_message(
        self,
        client_socket: socket,
        message: Optional[str] = "",
        event: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        logger.debug("Sending Message")

        if event != "":
            full_message = f"{event}:{message}"
            frames = self._frame_encoder.encode_payload_to_frames(
                payload=full_message, opcode=opcode
            )

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=message, opcode=opcode
        )

        for frame in frames:
            client_socket.send(frame)

    def ping(self, client_socket: socket) -> None:
        self.send_websocket_message(
            client_socket=client_socket, opcode=self.control_frame_types.ping
        )

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def join_room(self, client_socket, room_name) -> None:
        if room_name not in self._rooms:
            self._rooms[room_name] = set()
        self._rooms[room_name].add(client_socket)

    def leave_room(self, client_socket, room_name) -> None:
        if room_name in self._rooms and client_socket in self._rooms[room_name]:
            self._rooms[room_name].remove(client_socket)

    def broadcast_to_room(self, room_name, message) -> None:
        if room_name in self._rooms:
            for client_socket in self._rooms[room_name]:
                self.send_websocket_message(message, client_socket=client_socket)
