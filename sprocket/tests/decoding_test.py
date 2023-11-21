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
from sprocket import WebsocketFrameDecoder


class TestWebSocketFrameEncoder(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create an instance of each class.
        """
        self.default_decoder = WebsocketFrameDecoder(status=True)
        self.server_decoder = WebsocketFrameDecoder(status=False)

    def test_masked_init(self):
        self.assertTrue(self.default_decoder.status)
        self.assertEqual(self.default_decoder._fin, 0)
        self.assertEqual(self.default_decoder._rsv1, 0)
        self.assertEqual(self.default_decoder._rsv2, 0)
        self.assertEqual(self.default_decoder._rsv3, 0)
        self.assertEqual(self.default_decoder._opcode, 0)
        self.assertEqual(self.default_decoder._mask, 0)
        self.assertEqual(self.default_decoder._payload_length, 0)
        self.assertIsNone(self.default_decoder._mask_key)
        self.assertEqual(self.default_decoder._payload_data, b"")

    def test_unmasked_init(self):
        self.assertFalse(self.server_decoder.status)
        self.assertEqual(self.server_decoder._fin, 0)
        self.assertEqual(self.server_decoder._rsv1, 0)
        self.assertEqual(self.server_decoder._rsv2, 0)
        self.assertEqual(self.server_decoder._rsv3, 0)
        self.assertEqual(self.server_decoder._opcode, 0)
        self.assertEqual(self.server_decoder._mask, 0)
        self.assertEqual(self.server_decoder._payload_length, 0)
        self.assertIsNone(self.server_decoder._mask_key)
        self.assertEqual(self.server_decoder._payload_data, b"")

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

    def test_masked_decoding(self) -> None:
        hex_sequence = [
            0x81,
            0x85,
            0x37,
            0xFA,
            0x21,
            0x3D,
            0x7F,
            0x9F,
            0x4D,
            0x51,
            0x58,
        ]
        data = bytearray(hex_sequence)

        self.server_decoder.decode_websocket_message(data_in_bytes=data)

        decoded_data_2 = self.server_decoder.payload_data.decode()
        self.assertEqual(bytearray(b"7\xfa!="), self.server_decoder._mask_key)
        self.assertEqual("Hello", decoded_data_2)

    def test_unmasked_decoding(self) -> None:
        hex_sequence_1 = [0x81, 0x05, 0x48, 0x65, 0x6C, 0x6C, 0x6F]
        hex_sequence_2 = [
            0x81,
            0x0B,
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
            0x20,
            0x57,
            0x6F,
            0x72,
            0x6C,
            0x64,
        ]

        data_1 = bytearray(hex_sequence_1)
        data_2 = bytearray(hex_sequence_2)

        self.default_decoder.decode_websocket_message(data_in_bytes=data_1)

        decoded_data_1 = self.default_decoder.payload_data.decode()

        self.assertEqual("Hello", decoded_data_1)

        self.default_decoder.decode_websocket_message(data_in_bytes=data_2)

        decoded_data_2 = self.default_decoder.payload_data.decode()

        self.assertEqual("Hello World", decoded_data_2)
