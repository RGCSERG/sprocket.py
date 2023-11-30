from sprocket import ServerSocketImpl
import socket
from loguru import logger

io = ServerSocketImpl()


def main(socket: socket):
    def on_join(room_name: str):
        logger.success(room_name)
        io.join_room(room_name=room_name, socket=socket)

    def on_send(message):
        logger.success(message)
        io.to(room_name=message["room_ID"]).emit("recieve_message", payload=message)

    io.on("join_room", on_join)
    io.on("send_message", on_send)


io.on("connection", main)

if __name__ == "__main__":
    io.start()
