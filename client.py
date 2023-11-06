import time

from loguru import logger
from pydantic import BaseModel
from sprocket import ClientSocketImpl

client = ClientSocketImpl()
messages = []


# def stuff_will_happen(args, kwargs):
#     client.send_websocket_message(message="aint no way")
#     client.send_websocket_message(message="aint no way2")
#     client.send_websocket_message(message="aint no way3" event="send_message")
#     client.close()
class Message(BaseModel):
    owner_id: int
    message: str
    room_name: str


def prints(args, kwargs):
    dictt = eval(args.replace("'", '"'))
    message = Message(**dictt)
    messages.append(message.message)
    print(messages)


# client.on("send_message", stuff_will_happen)
client.on("recieved_message", prints)


if __name__ == "__main__":
    client.start()
    client.send_websocket_message(message="room1", event="join_room")

while True:
    inn = int(input("1 or 0: "))
    if inn:
        message = input("what the heeeeeeeeeeeeeeel: ")
        messages.append(message)
        message = {
            "owner_id": client.ID,
            "message": message,
            "room_name": "room1",
        }
        client.send_websocket_message(message=str(message), event="send_message")
    else:
        client.close()
