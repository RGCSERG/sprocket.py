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
from .maskkeygenerator import *

__all__: Final[List[str]] = ["WebSocketFrameEncoder"]


class WebSocketFrameEncoder:
    def __init__(self, max_frame_size: Optional[int] = 125):
        # Constructor for the WebSocketFrameEncoder class.
        # It initializes the maximum frame size parameter.
        self.max_frame_size = max_frame_size
        self.mask_key_generator = CustomRandomGenerator()

    def _generate_frame(self, payload, opcode, fin, mask):
        # Private method to generate a single WebSocket frame.
        frame = bytearray()
        payload_length = len(payload)

        if payload_length <= 125:
            # For payloads with length <= 125, use a 7-bit payload length representation.
            frame.append((fin << 7) | opcode)
            if mask:
                frame.append((mask << 7) | payload_length)
                mask_key = self.mask_key_generator.generate_masking_key()
                frame.extend(mask_key)
                masked_payload = bytes(
                    payload[i] ^ mask_key[i % 4] for i in range(payload_length)
                )
                frame.extend(masked_payload)
            else:
                frame.append(payload_length)
                frame.extend(payload)
        elif (
            payload_length <= 0xFFFF
        ):  # payload length that is less than or equal to 65535
            # For payloads with length <= 0xFFFF, use a 16-bit payload length representation.
            frame.append((fin << 7) | opcode)
            frame.append((mask << 7) | 126)
            frame.extend(payload_length.to_bytes(2, byteorder="big"))
            if mask:
                mask_key = self.mask_key_generator.generate_masking_key()
                frame.extend(mask_key)
                masked_payload = bytes(
                    payload[i] ^ mask_key[i % 4] for i in range(payload_length)
                )
                frame.extend(masked_payload)
            else:
                frame.extend(payload)
        else:
            # payload length is greater than 65535
            # For payloads with length > 0xFFFF, use a 64-bit payload length representation.
            frame.append((fin << 7) | opcode)
            frame.append((mask << 7) | 127)
            frame.extend(payload_length.to_bytes(8, byteorder="big"))
            if mask:
                mask_key = self.mask_key_generator.generate_masking_key()
                frame.extend(mask_key)
                masked_payload = bytes(
                    payload[i] ^ mask_key[i % 4] for i in range(payload_length)
                )
                frame.extend(masked_payload)
            else:
                frame.extend(payload)

        return frame

    def encode_payload_to_frames(self, payload):
        # Public method to encode a payload into a list of WebSocket frames.
        self.payload = payload.encode("utf-8")
        self.payload_length = len(self.payload)
        frames = []

        if self.payload_length <= self.max_frame_size:
            # If payload fits within the maximum frame size, create a single frame.
            frames.append(self._generate_frame(self.payload, 1, 1, 1))
        else:
            # If payload exceeds the maximum frame size, split it into multiple frames.
            for i in range(0, self.payload_length, self.max_frame_size):
                frame_payload = self.payload[i : i + self.max_frame_size]
                fin = 0 if (i + self.max_frame_size) < self.payload_length else 1
                opcode = 0 if i == 0 else 0x00
                frames.append(self._generate_frame(frame_payload, opcode, fin, 1))

        return frames
