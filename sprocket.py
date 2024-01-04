from sprocket import ServerSocket
import socket
from loguru import logger

io = ServerSocket()

io.enable_cors_middleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


def main(socket):
    def on_join(room_name: str):
        logger.success(room_name)
        socket.join_room(room_name=room_name)

    def on_send(message):
        logger.success(message)
        socket.to(room_name=message["room_ID"]).emit("recieve_message", payload=message)

    socket.on("join_room", on_join)
    socket.on("send_message", on_send)


io.on("connection", main)

if __name__ == "__main__":
    io.start()
