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

import socket, threading
from typing import Callable, Final, List, Optional, Type
from loguru import logger
from .serversocketbase import *

__all__: Final[List[str]] = ["ServerSocketImpl"]


class ServerSocketImpl(
    ServerSocketBaseImpl
):  # rework with new frame encoder and websocketframe class updates + comments
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
        """
        Starts the WebSocket server and listens for incoming connections.
        This method listens for incoming connections on the specified host and port,
        and starts a separate thread to handle incoming messages from each client instance.
        """
        self._server_socket.listen(
            self._BACKLOG
        )  # Start listening proccess, specifiying maxiumum queue.
        logger.success(f"Listening on port: {self._PORT}")  # Return log message.

        listen_thread = threading.Thread(
            target=self._listen_for_messages
        )  # Initialise listening thread.
        self.main_thread = True  # Set thread base case.
        listen_thread.start()  # Start listening thread.

    def broadcast_message(
        self, event: Optional[str] = "", payload: (str | bytes | dict | None) = ""
    ) -> None:
        """
        Broadcast a message to all connected WebSocket clients.
        This method sends a message to all WebSocket clients currently connected to the server.

        Args:
            payload Optional[str]: The message to broadcast to clients.
        """
        for socket in self._ws_sockets:  # For each active socket.
            try:
                self._emit(
                    event=event, socket=socket, payload=payload
                )  # Emit the message.
            except Exception as e:
                # Handle any errors or disconnections here
                logger.warning(f"Error broadcasting message to client: {e}")

    def ping(self, socket: socket) -> None:
        """
        Send a WebSocket Ping frame to a specific client.
        This method sends a WebSocket Ping frame to a specific client, prompting a Pong response.

        Args:
            socket socket: The client socket to send the Ping frame to.
        """
        self._send_websocket_message(
            socket=socket, opcode=self.control_frame_types.ping
        )  # Send a ping frame to the client socket.

    def on(self, event: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event.
        This method allows registering custom event handlers to respond to specific events.

        Args:
            event str: The event to listen for.
            handler Callable: The function to be executed when the event occurs.
        """
        if event not in self._event_handlers:  # If event not found.
            self._event_handlers[
                event
            ] = []  # Append it to the _event_handlers dictionary.
        self._event_handlers[event].append(
            handler
        )  # Then append the provided handler to the dictionary entry.

    def join_room(self, room_name: str, socket: socket) -> None:
        """
        Add a client to a specific chat room.
        This method adds a client (identified by their socket) to a specified chat room.

        Args:
            socket socket: The client socket to be added to the chat room.
            room_name str: The name of the chat room to join.
        """
        if room_name not in self._rooms:  # If the room name does not exist.
            self._rooms[room_name] = []  # Create the room with the provided name.
        self._rooms[room_name].append(socket)  # Append the client socket to the room.

    def to(
        self, room_name: str
    ) -> Type["RoomEmitter"]:  # Type is used here to avoid undefined errors.
        """
        Emits a message to a specific room, with use of the RoomEmitter class defined below.

        Args:
            room_name str: The specific room to be emitted to.

        Returns:
            RoomEmitter: Returns an instance of the room emitter class.
        """
        if room_name not in self._rooms:  # Implement some error handling logic.
            self._rooms[room_name] = []  # Not a viable solution.

        room_users: list = self._rooms[
            room_name
        ]  # Set list of sockets to list room_users.

        return RoomEmitter(server_socket=self, room_users=room_users)

    def leave_room(self, socket: socket, room_name: Optional[str] = "") -> None:
        """
        Remove a client from a specific chat room.
        This method removes a client (identified by their socket) from a specified chat room.

        Args:
            socket socket: The client socket to be removed from the chat room.
            room_name str: The name of the chat room to leave.
        """
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
        """
        Shuts down the server socket, without forcing clients to close connection.
        """
        for socket in self._active_sockets:  # For each active socket.
            self._close_socket(socket=socket)  # Send a control close connection frame.
        self.main_thread = False  # Terminate the server listening thread.


class RoomEmitter:
    """
    Allows for messages to be emitted to a particular room,
    not just all or one client.
    """

    def __init__(self, server_socket: ServerSocketImpl, room_users: list) -> None:
        """
        Initialiser method

        Args:
            server_socket ServerSocketImpl: The current instance of the server.
            room list: The list of sockets in the specified room.
        """
        self._server_socket = server_socket  # Initialise instance of the server.
        self._room_users: list = room_users  # Initialise room's socket list.

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        """
        Method used for emitting message to specific room, with use of the private _emit message,
        with respect to the current instance of the ServerSocketImpl instance.

        Args:
            event str: The event to be trigger by the sent message.
            payload (str | bytes | dict | None): The payload to be sent with the WebSocket message,
            the specific type of the payload doesn't matter (too much) as will be automatically converted
            to str by the _emit function.
        """
        for socket in self._room_users:  # Iterates through each socket in the room.
            self._server_socket._emit(
                event=event, socket=socket, payload=payload
            )  # For each socket in the room, a message is directly sent.
