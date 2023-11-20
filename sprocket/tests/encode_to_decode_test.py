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

import unittest
from sprocket import WebSocketFrameEncoder, WebsocketFrameDecoder


class TestEncodeToDecode(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create an instance of each class, one masked one not.
        """
        self.encoder_masked = WebSocketFrameEncoder(IS_MASKED=True)
        self.encoder_unmasked = WebSocketFrameEncoder(IS_MASKED=False)
        self.default_decoder = WebsocketFrameDecoder()
        self.server_decoder = WebsocketFrameDecoder(status=False)

    def _decode_message(self, frames: list) -> str:
        data_in_bytes = b""
        final_message = ""

        for frame in frames:
            data_in_bytes = frame
            if not self._is_final_frame(data_in_bytes):
                # This is a fragmented frame
                self.decoder.decode_websocket_message(data_in_bytes=data_in_bytes)
                message_payload = self.decoder.payload_data
                final_message += message_payload.decode("utf-8")
            else:
                # This is a non-fragmented frame
                self.decoder.decode_websocket_message(data_in_bytes=data_in_bytes)
                message_payload = self.decoder.payload_data
                final_message += message_payload.decode("utf-8")

        if final_message and data_in_bytes:
            data_in_bytes = b""
            return final_message

    def _is_final_frame(self, data_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (data_in_bytes[0] & 0b10000000) >> 7 == 1

    def test_unmasked_encoding_decoding(self) -> None:
        payload_1 = "Hello"
        payload_2 = "Hello" * 12**4
        payload_3 = "{'json_data': 1}"

        data_1 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_1)
        data_2 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_2)
        data_3 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_3)

        self.server_decoder.decode_websocket_message(data_in_bytes=data_1)
        decoded_data_1 = self.server_decoder.payload_data.decode()

        self.server_decoder.decode_websocket_message(data_in_bytes=data_2)
        decoded_data_2 = self.server_decoder.payload_data.decode()

        self.server_decoder.decode_websocket_message(data_in_bytes=data_3)
        decoded_data_3 = self.server_decoder.payload_data.decode()

        self.assertEqual(payload_1, decoded_data_1)
        self.assertEqual(payload_2, decoded_data_2)
        self.assertEqual(payload_3, decoded_data_3)

    def test_masked_encoding_decoding(self) -> None:
        payload_1 = "Hello"
        payload_2 = "Hello" * 12**4
        payload_3 = "{'json_data': 1}"

        data_1 = self.encoder_masked.encode_payload_to_frames(payload=payload_1)
        data_2 = self.encoder_masked.encode_payload_to_frames(payload=payload_2)
        data_3 = self.encoder_masked.encode_payload_to_frames(payload=payload_3)

        self.default_decoder.decode_websocket_message(data_in_bytes=data_1)
        decoded_data_1 = self.default_decoder.payload_data.decode()

        self.default_decoder.decode_websocket_message(data_in_bytes=data_2)
        decoded_data_2 = self.default_decoder.payload_data.decode()

        self.default_decoder.decode_websocket_message(data_in_bytes=data_3)
        decoded_data_3 = self.default_decoder.payload_data.decode()

        self.assertEqual(payload_1, decoded_data_1)
        self.assertEqual(payload_2, decoded_data_2)
        self.assertEqual(payload_3, decoded_data_3)
