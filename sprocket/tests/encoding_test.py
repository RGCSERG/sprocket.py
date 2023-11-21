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
from sprocket import WebSocketFrameEncoder


class TestWebSocketFrameEncoder(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create an instance of each class, one masked one not.
        """
        self.encoder_masked = WebSocketFrameEncoder(IS_MASKED=True)
        self.encoder_unmasked = WebSocketFrameEncoder(IS_MASKED=False)

    def test_init_masked(self) -> None:
        self.assertEqual(self.encoder_masked.MAX_FRAME_SIZE, 125)
        self.assertEqual(self.encoder_masked.IS_MASKED, True)
        self.assertIsNotNone(self.encoder_masked.mask_key_generator)

    def test_init_unmasked(self) -> None:
        self.assertEqual(self.encoder_unmasked.MAX_FRAME_SIZE, 125)
        self.assertEqual(self.encoder_unmasked.IS_MASKED, False)
        self.assertIsNotNone(self.encoder_unmasked.mask_key_generator)

    def test_masked_encoding(self) -> None:
        hex_sequence = [
            0x81,
            0x05,
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

    def test_unmasked_encoding(self) -> None:
        hex_sequence = [0x81, 0x05, 0x48, 0x65, 0x6C, 0x6C, 0x6F]
        data = bytearray(hex_sequence)

        payload_1 = "Hello"
        payload_2 = "Hello" * 12**4
        payload_3 = "{'json_data': 1}"

        # Encode payloads.
        data_1 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_1)
        data_2 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_2)
        data_3 = self.encoder_unmasked.encode_payload_to_frames(payload=payload_3)

        self.assertEqual(data, data_1[0])
