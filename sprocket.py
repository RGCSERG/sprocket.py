import socket
import time
from loguru import logger

from pydantic import BaseModel
from sprocket import ServerSocketImpl


server = ServerSocketImpl()


def deal_with_stuff(args, kwargs):
    server.join_room(args, kwargs)


class Message(BaseModel):
    owner_id: int
    message: str
    room_name: str


def send(args, kwargs):
    message = Message(**eval(args.replace("'", '"')))

    server.broadcast_to_room(
        message=str(dict(message)),
        client_socket=kwargs,
        event="recieved_message",
        room_name=message.room_name,
    )


def main(socket: socket):
    logger.success(f"socket {socket} connected")


server.on("connect", main)
server.on("join_room", deal_with_stuff)
server.on("send_message", send)

if __name__ == "__main__":
    server.start()

# class SocketConnected:
#     def __init__(self, socket:socket) -> None:
#         self.socket = socket
#         self.socket.on?

#     def start(self):
"""Maybe implement this approach?"""
