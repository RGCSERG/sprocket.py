import time
from sprocket import ClientSocketImpl

client = ClientSocketImpl()


def stuff_will_happen(message):
    print(message)

    client.send_websocket_message(message="aint no way", event="stuff")
    client.close()


client.on("stuff", stuff_will_happen)


if __name__ == "__main__":
    client.start()
    client.send_websocket_message(message="yooo", event="stuff")
