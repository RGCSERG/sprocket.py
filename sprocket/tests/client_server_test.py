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

import time
import socket
from typing import List
import unittest
from sprocket import ClientSocketImpl, ServerSocketImpl


class ClientServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.messages: List[str] = []
        self.client: ClientSocketImpl = ClientSocketImpl()
        self.server: ServerSocketImpl = ServerSocketImpl()

    def test_message_delivery(self) -> None:
        def main(socket: socket) -> None:
            def on_join(room_name: str) -> None:
                self.server.join_room(room_name=room_name, socket=socket)

            def on_send(message) -> None:
                self.server.to(room_name=message["room_ID"]).emit(
                    "recieve_message", payload=message
                )

            self.server.on("join_room", on_join)
            self.server.on("send_message", on_send)

        self.server.on("connection", main)

        self.server.start()

        def on_recieve(message):
            self.messages.append(message["message"])

        self.client.on("recieve_message", on_recieve)

        self.client.start()

        self.client.emit("join_room", "1234")
        self.client.emit("send_message", {"message": "big money", "room_ID": "1234"})

        time.sleep(1)

        self.assertEqual("big money", self.messages)

        self.server.stop()
