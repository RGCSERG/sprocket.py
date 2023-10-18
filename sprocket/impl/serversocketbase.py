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

import select, socket, threading, time
from typing import Final, List, Optional
from loguru import logger
from ..models.websocketframe import *
from ..models.frameencoder import *
from ..models.controlframes import *

__all__: Final[List[str]] = ["ServerSocketBaseImpl"]


class ServerSocketBaseImpl:
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,  # add error checking
        IS_MASKED: Optional[bool] = True,
        TIMEOUT: Optional[int] = 5,
    ) -> None:
        self.TCP_HOST = TCP_HOST

        if TCP_PORT is not None and not (1 <= TCP_PORT <= 65535):
            raise ValueError("TCP_PORT must be in the range of 1-65535.")
        self.TCP_PORT = TCP_PORT
        self.TIMEOUT = TIMEOUT
        self.event_handlers = {}
        self.rooms = {}
        self.TCP_BUFFER_SIZE = TCP_BUFFER_SIZE
        self.WS_ENDPOINT = WS_ENDPOINT
        self.lock = threading.Lock()
        self.frame_decoder = WebsocketFrame()
        self.frame_encoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=IS_MASKED
        )
        self.control_frame_types = ControlFrame()

    def join_room(self, client_socket, room_name):
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        self.rooms[room_name].add(client_socket)

    def leave_room(self, client_socket, room_name):
        if room_name in self.rooms and client_socket in self.rooms[room_name]:
            self.rooms[room_name].remove(client_socket)

    def broadcast_to_room(self, room_name, message):
        if room_name in self.rooms:
            for client_socket in self.rooms[room_name]:
                self.send_websocket_message(message, client_socket=client_socket)

    def _check_control_frame(self, opcode: bytes, client_socket: socket) -> None:
        if opcode == self.control_frame_types.close:
            self._close_socket(client_socket=client_socket)
            return
        if opcode == self.control_frame_types.ping:
            logger.debug(f"Recived Ping from {client_socket}")
            self._pong(client_socket=client_socket)
            return
        if opcode == self.control_frame_types.pong:
            logger.debug(f"Recived Pong from {client_socket}")
            return

    def _pong(self, client_socket: socket) -> None:
        self.send_websocket_message(
            client_socket=client_socket, opcode=self.control_frame_types.pong
        )

    def ping(self, client_socket: socket) -> None:
        self.send_websocket_message(
            client_socket=client_socket, opcode=self.control_frame_types.ping
        )

    def on(self, event, handler):
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def _trigger(self, event, *args, **kwargs):
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                handler(*args, **kwargs)

    def _handle_websocket_message(self, client_socket: socket) -> None:
        data_in_bytes = b""
        final_message = ""

        while True:
            frame_data = self._read_recv(client_socket=client_socket)
            if not frame_data:
                # Connection closed, or no data received.
                break

            logger.debug("Handling websocket message")

            data_in_bytes = frame_data
            if not self._is_final_frame(data_in_bytes):
                # This is a fragmented frame
                self.frame_decoder.populateFromWebsocketFrameMessage(data_in_bytes)
                message_payload = self.frame_decoder.get_payload_data()
                final_message += message_payload.decode("utf-8")
            else:
                # This is a non-fragmented frame
                self.frame_decoder.populateFromWebsocketFrameMessage(data_in_bytes)
                control_opcode = self.frame_decoder.get_control_opcode()
                self._check_control_frame(
                    opcode=control_opcode, client_socket=client_socket
                )
                message_payload = self.frame_decoder.get_payload_data()
                final_message += message_payload.decode("utf-8")
                break

        if final_message and data_in_bytes:
            logger.debug(f"Received message: {final_message}")
            data_in_bytes = b""
            self._trigger("message", final_message, client_socket)

    def _is_final_frame(self, data_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (data_in_bytes[0] & 0b10000000) >> 7 == 1

    def send_websocket_message(
        self,
        message: Optional[str] = "",
        opcode: Optional[bytes] = None,
        client_socket=socket,
    ) -> None:
        frames = self.frame_encoder.encode_payload_to_frames(
            payload=message, opcode=opcode
        )

        for frame in frames:
            client_socket.send(frame)

    def _close_socket(self, client_socket: socket) -> None:
        with self.lock:
            logger.warning("closing socket")
            if client_socket in self.ws_sockets:
                self.ws_sockets.remove(client_socket)
            self.input_sockets.remove(client_socket)
            self.send_websocket_message(
                client_socket=client_socket, opcode=self.control_frame_types.close
            )
            client_socket.close()
            return

    def _read_recv(self, client_socket: socket) -> None:
        if hasattr(self, "input_sockets"):
            readable_sockets = select.select(self.input_sockets, [], [], self.TIMEOUT)[
                0
            ]
        else:
            readable_sockets = select.select([client_socket], [], [], self.TIMEOUT)[0]

        if client_socket not in readable_sockets:
            return

        with self.lock:
            retry_count = 0
            max_retries = 5

            while retry_count < max_retries:
                data = client_socket.recv(self.TCP_BUFFER_SIZE)
                if data:
                    return data
                else:
                    retry_count += 1
                    delay = 2**retry_count
                    print(f"No data received, retrying in {delay} seconds...")
                    time.sleep(delay)

            logger.warning("Max retries reached. Unable to read data.")
            return
