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


__all__: Final[List[str]] = ["WebSocketFrameEncoder"]


class CustomRandomGenerator:
    def random(self):
        self.seed = (self.seed * 1664525 + 1013904223) & 0xFFFFFFFF
        return (self.seed >> 24) & 0xFF

    def generate_masking_key(self, seed=1234):
        self.seed = seed
        masking_key = bytearray(self.random() for _ in range(4))
        return masking_key


class WebSocketFrameEncoder:
    def __init__(
        self, MAX_FRAME_SIZE: Optional[int] = 125, IS_MASKED: Optional[bool] = True
    ):
        # Constructor for the WebSocketFrameEncoder class.
        # It initializes the maximum frame size parameter.
        self.MAX_FRAME_SIZE = MAX_FRAME_SIZE
        self.mask_key_generator = CustomRandomGenerator()
        self.IS_MASKED = IS_MASKED

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
                print(masked_payload)
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

        if self.payload_length <= self.MAX_FRAME_SIZE:
            # If payload fits within the maximum frame size, create a single frame.
            frames.append(self._generate_frame(self.payload, 1, 1, self.IS_MASKED))
        else:
            # If payload exceeds the maximum frame size, split it into multiple frames.
            for i in range(0, self.payload_length, self.MAX_FRAME_SIZE):
                frame_payload = self.payload[i : i + self.MAX_FRAME_SIZE]
                fin = 0 if (i + self.MAX_FRAME_SIZE) < self.payload_length else 1
                opcode = 0 if i == 0 else 0x00
                frames.append(
                    self._generate_frame(frame_payload, opcode, fin, self.IS_MASKED)
                )

        return frames


class WebsocketFrame:
    """Python class that represents a simple WebSocket frame.
    Provides methods for parsing WebSocket frame messages,
    extracting its components, and returning the payload data."""

    def __init__(self) -> None:
        self._fin = 0
        self._rsv1 = 0
        self._rsv2 = 0
        self._rsv3 = 0
        self._opcode = 0
        self._mask = 0
        self._payload_length = 0
        self._mask_key = None
        self._payload_data = b""

    def populateFromWebsocketFrameMessage(self, data_in_bytes) -> None:
        self._parse_flags(data_in_bytes)
        self._parse_payload_length(data_in_bytes)
        self._maybe_parse_masking_key(data_in_bytes)
        self._parse_payload(data_in_bytes)

    def _parse_flags(self, data_in_bytes) -> None:
        first_byte = data_in_bytes[0]
        self._fin = (first_byte & 0b10000000) >> 7
        self._rsv1 = (first_byte & 0b01000000) >> 6
        self._rsv2 = (first_byte & 0b00100000) >> 5
        self._rsv3 = (first_byte & 0b00010000) >> 4
        self._opcode = first_byte & 0b00001111

        second_byte = data_in_bytes[1]
        self._mask = (second_byte & 0b10000000) >> 7

    def _parse_payload_length(self, data_in_bytes) -> None:
        payload_length = data_in_bytes[1] & 0b01111111
        mask_key_start = 2

        if payload_length == 126:
            payload_length = int.from_bytes(data_in_bytes[2:4], byteorder="big")
            mask_key_start = 4
        elif payload_length == 127:
            payload_length = int.from_bytes(data_in_bytes[2:10], byteorder="big")
            mask_key_start = 10

        self._payload_length = payload_length
        self._mask_key_start = mask_key_start

    def _maybe_parse_masking_key(self, data_in_bytes) -> None:
        if self._mask:
            self._mask_key = data_in_bytes[
                self._mask_key_start : self._mask_key_start + 4
            ]

    def _parse_payload(self, data_in_bytes) -> None:
        payload_data = b""
        if self._payload_length > 0:
            payload_start = self._mask_key_start if self._mask else self._mask_key_start
            encoded_payload = data_in_bytes[
                payload_start : payload_start + self._payload_length + 4
            ]

            if self._mask:
                decoded_payload = [
                    byte ^ self._mask_key[i % 4]
                    for i, byte in enumerate(encoded_payload)
                ]
                payload_data = bytes(decoded_payload)
            else:
                payload_data = encoded_payload

        self._payload_data = payload_data

    def get_payload_data(self) -> bytes:
        return self._payload_data

    def get_control_opcode(self) -> int:
        return self._opcode


class WebSocketBaseImpl:
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
    ) -> None:
        self.TCP_HOST = TCP_HOST

        if TCP_PORT is not None and not (1 <= TCP_PORT <= 65535):
            raise ValueError("TCP_PORT must be in the range of 1-65535.")
        self.TCP_PORT = TCP_PORT

        self.TCP_BUFFER_SIZE = TCP_BUFFER_SIZE
        self.WS_ENDPOINT = WS_ENDPOINT
        self.frame_decoder = WebsocketFrame()
        self.frame_encoder = WebSocketFrameEncoder()

    def _handle_websocket_message(self, datas):
        data_in_bytes = b""
        final_message = ""

        for data in datas:
            frame_data = data
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
