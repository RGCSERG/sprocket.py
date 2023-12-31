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


import socket, threading, json  # Import used libaries.
from typing import (
    Callable,
    Final,
    List,
    Optional,
    Type,
)  # Used for type annotations and decloration.
from loguru import logger
from .sprocketsocketbase import SprocketSocketBase
from ..frame_models import FrameOpcodes  # Import used classes.
from ..rooms import *

__all__: Final[List[str]] = ["SprocketSocket"]


class SprocketSocket(SprocketSocketBase):
    def __init__(
        self,
        SOCKET: socket,
        PARENT_SERVER,
        MAX_FRAME_SIZE: Optional[int] = 125,
        BUFFER_SIZE: Optional[int] = 8192,
    ) -> None:
        super().__init__(
            SOCKET=SOCKET,
            PARENT_SERVER=PARENT_SERVER,
            MAX_FRAME_SIZE=MAX_FRAME_SIZE,
            BUFFER_SIZE=BUFFER_SIZE,
        )

    def start_listening_thread(self) -> None:
        listen_thread = threading.Thread(
            target=self._listen_for_messages
        )  # Open a listening thread.

        listen_thread.start()  # Start the listening thread.

        return

    def start_heartbeat(self) -> None:
        heartbeat_thread = threading.Thread(
            target=self._heartbeat
        )  # Open a heartbeat thread.

        heartbeat_thread.start()  # Start the heartbeat thread.

        return

    def close(self) -> None:
        logger.warning("Sending Close Frame")

        if (
            self in self._PARENT_SERVER._websocket_sockets
        ):  # If the socket is not already closed.
            self._send_websocket_message(
                opcode=FrameOpcodes.close
            )  # Send a close frame.

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
            with self._LOCK:
                self.SOCKET.send(frame)  # Send it to the server.

        return

    def join_room(self, room_name):
        room = self._PARENT_SERVER._rooms.get(room_name)
        if room is None:
            room = WebSocketRoom(name=room_name)
            self._PARENT_SERVER.rooms[room_name] = room
        self.rooms_joined.add(room)
        room.add_member(self)

    def to(
        self, room_name: str
    ) -> Type["RoomEmitter"]:  # Type is used here to avoid undefined errors.
        if room_name not in self._joined_rooms:  # If the room does not exist.
            logger.warning(
                f"Room with id: {room_name}, does not exist."
            )  # Log the error.

        room_users: list = (
            self._rooms[room_name] if room_name in self._rooms else []
        )  # Set list of sockets to list room_users.

        return RoomEmitter(server_socket=self, room_users=room_users)


class RoomEmitter:
    """
    Allows for messages to be emitted to a particular room,
    not just all or one client.
    """

    def __init__(self, sprocket_socket: SprocketSocket, room_users: list) -> None:
        """
        Initialiser method.

        Args:
            sprocket_socket SprocketSocket: The current instance of the socket.
            room list: The list of sockets in the specified room.
        """
        self.sprocket_socket: SprocketSocket = (
            sprocket_socket  # Initialise instance of the socket.
        )
        self._room_users: List[
            SprocketSocket
        ] = room_users  # Initialise room's socket list.

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        """
        Method used for emitting message to specific room, with use of the private emit method,
        with respect to the current instance of the Socket instance.

        Args:
            event str: The event to be trigger by the sent message.
            payload (str | bytes | dict | None): The payload to be sent with the WebSocket message,
            the specific type of the payload doesn't matter (too much) as will be automatically converted
            to str by the emit function.
        """

        for socket in self._room_users:  # Iterates through each socket in the room.
            if socket != self.sprocket_socket:
                socket.emit(
                    event=event, socket=socket, payload=payload
                )  # For each socket in the room, a message is directly sent.

        return
