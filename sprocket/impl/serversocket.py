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
        Starts the WebSocket server and listen for incoming connections.
        This method listens for incoming connections on the specified host and port,
        and starts a separate thread to handle incoming messages from each client instance.
        """
        self._server_socket.listen(self._BACKLOG)
        logger.debug(f"Listening on port: {self._PORT}")

        listen_thread = threading.Thread(target=self._listen_for_messages)
        self.main_thread = True
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
        for socket in self._ws_sockets:
            try:
                if event != "":
                    message = f"{event}:{message}"
                    frames = self._frame_encoder.encode_payload_to_frames(message)
                else:
                    frames = self._frame_encoder.encode_payload_to_frames(message)
                for frame in frames:
                    socket.send(frame)
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

    def join_room(self, room_name: str, socket: socket) -> None:
        """
        Add a client to a specific chat room.
        This method adds a client (identified by their socket) to a specified chat room.

        Args:
            socket socket: The client socket to be added to the chat room.
            room_name str: The name of the chat room to join.
        """
        if room_name not in self._rooms:
            self._rooms[room_name] = []
        self._rooms[room_name].append(socket)

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

        room_users: list = self._rooms[room_name]

        return RoomEmitter(server_socket=self, room_users=room_users)

    def leave_room(self, socket: socket, room_name: Optional[str] = "") -> None:
        """
        Remove a client from a specific chat room.
        This method removes a client (identified by their socket) from a specified chat room.

        Args:
            socket socket: The client socket to be removed from the chat room.
            room_name str: The name of the chat room to leave.
        """
        if room_name != "":
            if room_name in self._rooms and socket in self._rooms[room_name]:
                self._rooms[room_name].remove(socket)
        else:
            for room_name in self._rooms:
                if socket in self._rooms[room_name]:
                    self._rooms[room_name].remove(socket)

    def stop(self):
        for socket in self._active_sockets:
            self._close_socket(socket=socket)
        self.main_thread = False

    # def broadcast_to_room(
    #     self,
    #     room_name: str,
    #     message: str,
    #     client_socket: Optional[Any] = None,
    #     event: Optional[str] = "",
    # ) -> None:
    #     """
    #     Broadcast a message to all clients in a specific chat room.
    #     This method sends a message to all clients who are part of a specific chat room.

    #     Args:
    #         client_socket socket: The client socket which sent the message
    #         message str: The message to broadcast to clients in the chat room.
    #     """

    #     if self._rooms[room_name] and client_socket in self._rooms[room_name]:
    #         for socket in self._rooms[room_name]:
    #             if client_socket != socket:
    #                 self._send_websocket_message(
    #                     message=message, client_socket=socket, event=event
    #                 )


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
                event=event, payload=payload, socket=socket
            )  # For each socket in the room, a message is directly sent.
