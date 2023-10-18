import time

from loguru import logger
from sprocket import ClientSocketImpl

client = ClientSocketImpl()


# def stuff_will_happen(args, kwargs):
#     client.send_websocket_message(message="aint no way")
#     client.send_websocket_message(message="aint no way2")
#     client.send_websocket_message(message="aint no way3" event="send_message")
#     client.close()

# def prints(args, kwargs):
#     print(args, kwargs)

# client.on("send_message", stuff_will_happen)
# client.on("recieved_message", prints)


if __name__ == "__main__":
    client.start()
    client.send_websocket_message(message="room1", event="join_room")


while True:
    inn = int(input("1 or 0"))
    if inn:
        client.send_websocket_message(message="aint no way", event="send_message")
