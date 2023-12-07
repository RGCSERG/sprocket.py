"""Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Sofloggertware.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import socket, threading, json
from typing import Callable, Final, List, Optional, Type
from loguru import logger
from .serversocketbase import *

__all__: Final[List[str]] = ["ServerSocket"]


class ServerSocket(
    ServerSocketBaseImpl
):  # rework with new frame encoder and websocketframe class updates + comments
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
        super().__init__(
            HOST=HOST,
            PORT=PORT,
            BUFFER_SIZE=BUFFER_SIZE,
            WS_ENDPOINT=WS_ENDPOINT,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
            TIMEOUT=TIMEOUT,
            BACKLOG=BACKLOG,
        )

    def start(self) -> None:
        self._server_socket.listen(
            self._BACKLOG
        )  # Start listening proccess, specifiying maxiumum queue.
        logger.success(f"Listening on port: {self._PORT}")  # Return log message.

        listen_thread = threading.Thread(
            target=self._listen_for_messages
        )  # Initialise listening thread.
        self.main_thread = True  # Set thread base case.
        listen_thread.start()  # Start listening thread.

    def leave_room(self, socket: socket, room_name: Optional[str] = "") -> None:
        if (
            room_name in self._rooms and socket in self._rooms[room_name]
        ):  # If room name provided, and the socket in that room.
            self._rooms[room_name].remove(
                socket
            )  # Remove the socket from the provided room.
            return  # Return so no more code is run.

        for (
            room_name
        ) in (
            self._rooms
        ):  # If no room_name provided, iterate through every individual room.
            if (
                socket in self._rooms[room_name]
            ):  # If the socket is in the current room.
                self._rooms[room_name].remove(
                    socket
                )  # Remove the socket from the room.

    def stop(self):
        for socket in self._active_sockets:  # For each active socket.
            self._close_socket(socket=socket)  # Send a control close connection frame.
        self.main_thread = False  # Terminate the server listening thread.

    def join_room(self, room_name: str, socket: socket) -> None:
        if room_name not in self._rooms:  # If the room name does not exist.
            self._rooms[room_name] = []  # Create the room with the provided name.
        self._rooms[room_name].append(socket)  # Append the client socket to the room.

    def emit(
        self, event: str, socket: socket, payload: (str | bytes | dict | None) = ""
    ) -> None:
        json_data: dict = {event: payload}  # Set up the json_data.

        payload: str = json.dumps(json_data)  # Dump the json_data into str format.

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload
        )  # Encode the payload into WebSocket frames.

        for frame in frames:  # For each frame created.
            socket.send(frame)  # Send it to the given socket.

        return

    def broadcast_message(
        self, event: Optional[str] = "", payload: (str | bytes | dict | None) = ""
    ) -> None:
        for socket in self._ws_sockets:  # For each active socket.
            try:
                self.emit(
                    event=event, socket=socket, payload=payload
                )  # Emit the message.
            except Exception as e:
                # Handle any errors or disconnections here
                logger.warning(f"Error broadcasting message to client: {e}")

    def ping(self, socket: socket) -> None:
        self._send_websocket_message(
            socket=socket, opcode=self.control_frame_types.ping
        )  # Send a ping frame to the client socket.

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:  # If event not found.
            self._event_handlers[
                event
            ] = []  # Append it to the _event_handlers dictionary.
        self._event_handlers[event].append(
            handler
        )  # Then append the provided handler to the dictionary entry.

    def to(
        self, room_name: str
    ) -> Type["RoomEmitter"]:  # Type is used here to avoid undefined errors.
        if room_name not in self._rooms:  # Implement some error handling logic.
            self._rooms[room_name] = []  # Not a viable solution.

        room_users: list = self._rooms[
            room_name
        ]  # Set list of sockets to list room_users.

        return RoomEmitter(server_socket=self, room_users=room_users)


class RoomEmitter:
    """
    Allows for messages to be emitted to a particular room,
    not just all or one client.
    """

    def __init__(self, server_socket: ServerSocket, room_users: list) -> None:
        """
        Initialiser method.

        Args:
            server_socket ServerSocketImpl: The current instance of the server.
            room list: The list of sockets in the specified room.
        """
        self._server_socket = server_socket  # Initialise instance of the server.
        self._room_users: list = room_users  # Initialise room's socket list.

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        """
        Method used for emitting message to specific room, with use of the private emit message,
        with respect to the current instance of the ServerSocketImpl instance.

        Args:
            event str: The event to be trigger by the sent message.
            payload (str | bytes | dict | None): The payload to be sent with the WebSocket message,
            the specific type of the payload doesn't matter (too much) as will be automatically converted
            to str by the emit function.
        """
        for socket in self._room_users:  # Iterates through each socket in the room.
            self._server_socket.emit(
                event=event, socket=socket, payload=payload
            )  # For each socket in the room, a message is directly sent.
