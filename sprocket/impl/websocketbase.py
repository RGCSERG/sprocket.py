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

from typing import Final, List, Optional
from ..models.websocketframe import *
from ..models.frameencoder import *

__all__: Final[List[str]] = ["WebSocketBaseImpl"]


class WebSocketBaseImpl:
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,  # add error checking
        IS_MASKED: Optional[bool] = True,
    ) -> None:
        self.TCP_HOST = TCP_HOST

        if TCP_PORT is not None and not (1 <= TCP_PORT <= 65535):
            raise ValueError("TCP_PORT must be in the range of 1-65535.")
        self.TCP_PORT = TCP_PORT

        self.TCP_BUFFER_SIZE = TCP_BUFFER_SIZE
        self.WS_ENDPOINT = WS_ENDPOINT
        self.frame_decoder = WebsocketFrame()
        self.frame_encoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=IS_MASKED
        )

    def _handle_websocket_message(self, client_socket):
        data_in_bytes = b""
        final_message = ""

        while True:
            frame_data = client_socket.recv(self.TCP_BUFFER_SIZE)
            if not frame_data:
                # Connection closed, or no data received.
                break

            data_in_bytes = frame_data
            if not self._is_final_frame(data_in_bytes):
                # This is a fragmented frame
                self.frame_decoder.populateFromWebsocketFrameMessage(data_in_bytes)
                message_payload = self.frame_decoder.get_payload_data()
                final_message += message_payload.decode("utf-8")
            else:
                # This is a non-fragmented frame
                self.frame_decoder.populateFromWebsocketFrameMessage(data_in_bytes)
                message_payload = self.frame_decoder.get_payload_data()
                final_message += message_payload.decode("utf-8")

        print("Received message:", final_message)
        data_in_bytes = b""

    def _is_final_frame(self, data_in_bytes):
        # Check the FIN bit in the first byte of the frame.
        return (data_in_bytes[0] & 0b10000000) >> 7 == 1
