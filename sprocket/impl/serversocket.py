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

import socket, threading, json
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


class ServerSocketImpl(
    ServerSocketBaseImpl
):  # rework with new frame encoder and websocketframe class updates + comments
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
        DEFAULT_HTTP_RESPONSE: Optional[bytes] = DEFAULT_HTTP_RESPONSE,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        super().__init__(
            TCP_HOST=TCP_HOST,
            TCP_PORT=TCP_PORT,
            TCP_BUFFER_SIZE=TCP_BUFFER_SIZE,
            WS_ENDPOINT=WS_ENDPOINT,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
            TIMEOUT=TIMEOUT,
            DEFAULT_HTTP_RESPONSE=DEFAULT_HTTP_RESPONSE,
            BACKLOG=BACKLOG,
        )

    def start(self) -> None:
        """
        Starts the WebSocket server and listen for incoming connections.
        This method listens for incoming connections on the specified host and port,
        and starts a separate thread to handle incoming messages from each client instance.
        """
        self._server_socket.listen(self._BACKLOG)
        logger.debug(f"Listening on port: {self._TCP_PORT}")

        listen_thread = threading.Thread(target=self._listen_for_messages)
        listen_thread.start()

    def broadcast_message(
        self, message: Optional[str] = "", event: Optional[str] = ""
    ) -> None:
        """
        Broadcast a message to all connected WebSocket clients.
        This method sends a message to all WebSocket clients currently connected to the server.

        Args:
            message Optional[str]: The message to broadcast to clients.
        """
        for client_socket in self._ws_sockets:
            try:
                if event != "":
                    message = f"{event}:{message}"
                    frames = self._frame_encoder.encode_payload_to_frames(message)
                else:
                    frames = self._frame_encoder.encode_payload_to_frames(message)
                for frame in frames:
                    client_socket.send(frame)
            except Exception as e:
                # Handle any errors or disconnections here
                logger.warning(f"Error broadcasting message to client: {e}")

    def send_websocket_message(
        self,
        socket: socket,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Send a WebSocket message to a specific client.
        This method sends a WebSocket message to a specific client identified by the provided socket.

        Args:
            socket socket: The client socket to send the message to.
            message Optional[str]: The message to send to the client.
            event Optional[str]: An optional event identifier for the message.
            opcode Optional[bytes]: The WebSocket frame opcode.
        """
        logger.debug("Sending Message")

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload, opcode=opcode
        )

        for frame in frames:
            socket.send(frame)

    def ping(self, client_socket: socket) -> None:
        """
        Send a WebSocket Ping frame to a specific client.
        This method sends a WebSocket Ping frame to a specific client, prompting a Pong response.

        Args:
            client_socket socket: The client socket to send the Ping frame to.
        """
        self.send_websocket_message(
            client_socket=client_socket, opcode=self.control_frame_types.ping
        )

    def on(self, event: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event.
        This method allows registering custom event handlers to respond to specific events.

        Args:
            event str: The event to listen for.
            handler Callable: The function to be executed when the event occurs.
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def join_room(self, room_name: str, client_socket: socket) -> None:
        """
        Add a client to a specific chat room.
        This method adds a client (identified by their socket) to a specified chat room.

        Args:
            client_socket socket: The client socket to be added to the chat room.
            room_name str: The name of the chat room to join.
        """
        if room_name not in self._rooms:
            self._rooms[room_name] = []
        self._rooms[room_name].append(client_socket)

    def leave_room(self, client_socket: socket, room_name: Optional[str] = "") -> None:
        """
        Remove a client from a specific chat room.
        This method removes a client (identified by their socket) from a specified chat room.

        Args:
            client_socket socket: The client socket to be removed from the chat room.
            room_name str: The name of the chat room to leave.
        """
        if room_name != "":
            if room_name in self._rooms and client_socket in self._rooms[room_name]:
                self._rooms[room_name].remove(client_socket)
        else:
            for room_name in self._rooms:
                if client_socket in self._rooms[room_name]:
                    self._rooms[room_name].remove(client_socket)

    def broadcast_to_room(
        self,
        room_name: str,
        message: str,
        client_socket: Optional[Any] = None,
        event: Optional[str] = "",
    ) -> None:
        """
        Broadcast a message to all clients in a specific chat room.
        This method sends a message to all clients who are part of a specific chat room.

        Args:
            client_socket socket: The client socket which sent the message
            message str: The message to broadcast to clients in the chat room.
        """

        if self._rooms[room_name] and client_socket in self._rooms[room_name]:
            for socket in self._rooms[room_name]:
                if client_socket != socket:
                    self.send_websocket_message(
                        message=message, client_socket=socket, event=event
                    )

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        json_data: dict = {f"{event}", payload}

        payload: bytes = json.dumps(json_data)

        frames = self._frame_encoder.encode_payload_to_frames(payload=payload)

        for frame in frames:
            socket.send(frame)
