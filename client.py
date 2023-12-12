from sprocket import ClientSocketImpl

messages: list = []
io = ClientSocketImpl()


def on_recieve(message):
    messages.append(message["message"])


io.on("recieve_message", on_recieve)

io.start()

io.emit("join_room", "1234")
io.emit("send_message", {"message": "Testing 123{][][asd{]}]}", "room_ID": "1234"})
