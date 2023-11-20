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
from .maskkey import *
from ..exceptions import *


__all__: Final[List[str]] = ["WebsocketFrameDecoder"]


class WebsocketFrameDecoder:  # inherit from descriptor class + comments
    """Python class that represents a simple WebSocket frame.
    Provides methods for parsing WebSocket frame messages,
    extracting its components, and returning the payload data."""

    def __init__(self, status: Optional[bool] = True) -> None:
        self.status = status

        self._fin: int = 0
        self._rsv1: int = 0
        self._rsv2: int = 0
        self._rsv3: int = 0
        self._opcode: int = 0
        self._mask: int = 0
        self._payload_length: bytes = 0
        self._mask_key: bytearray = None
        self._payload_data: bytes = b""

    @property
    def payload_data(self) -> bytes:
        return self._payload_data

    @property
    def opcode(self) -> int:
        return self._opcode

    @staticmethod
    def _parse_fin_bit(first_byte: bytes) -> int:
        return (first_byte & 0x80) >> 7

    @staticmethod
    def _parse_rsv1_bit(first_byte: bytes) -> int:
        return (first_byte & 0x40) >> 6

    @staticmethod
    def _parse_rsv2_bit(first_byte: bytes) -> int:
        return (first_byte & 0x20) >> 5

    @staticmethod
    def _parse_rsv3_bit(first_byte: bytes) -> int:
        return (first_byte & 0x10) >> 4

    @staticmethod
    def _parse_opcode(first_byte: bytes) -> int:
        return first_byte & 0xF

    @staticmethod
    def _parse_mask(second_byte: bytes) -> int:
        return (second_byte & 0x80) >> 7

    @staticmethod
    def _parse_payload_length(data_in_bytes: bytearray):
        payload_length = data_in_bytes[1] & 0x7F
        start_mask_key = 2

        if payload_length == 0x7E:
            payload_length = int.from_bytes(data_in_bytes[2:4], byteorder="big")
            start_mask_key = 4
        if payload_length == 0x7F:
            payload_length = int.from_bytes(data_in_bytes[2:10], byteorder="big")
            start_mask_key = 10

        return payload_length, start_mask_key

    def _parse_websocket_frame_header(self, data_in_bytes: bytearray) -> None:
        first_byte = data_in_bytes[0]
        second_byte = data_in_bytes[1]

        self._fin = self._parse_fin_bit(first_byte=first_byte)
        self._rsv1 = self._parse_rsv1_bit(first_byte=first_byte)
        self._rsv2 = self._parse_rsv2_bit(first_byte=first_byte)
        self._rsv3 = self._parse_rsv3_bit(first_byte=first_byte)
        self._opcode = self._parse_opcode(first_byte=first_byte)
        self._mask = self._parse_mask(second_byte=second_byte)
        self._payload_length, self._start_mask_key = self._parse_payload_length(
            data_in_bytes=data_in_bytes
        )

    def _may_parse_masking_key(self, data_in_bytes: bytearray) -> None:
        if self._mask:
            self._mask_key = data_in_bytes[
                self._mask_key_start : self._mask_key_start + 4
            ]

    def _parse_payload(self, data_in_bytes: bytearray) -> None:
        payload_data = b""
        if self._payload_length > 0:
            payload_start = (
                self._mask_key_start if self._mask else self._mask_key_start + 4
            )
            encoded_payload = data_in_bytes[
                payload_start : payload_start + self._payload_length
            ]

            if self._mask:
                MaskKey.decode_payload(
                    encoded_payload=encoded_payload, mask_key=self._mask_key
                )
            else:
                payload_data = encoded_payload

        self._payload_data = payload_data

    def _may_fail(self) -> bool:
        if self._mask == self.status:
            return True
        return False

    def decode_websocket_message(self, data_in_bytes: bytes) -> None:
        self._parse_websocket_frame_header(data_in_bytes=data_in_bytes)
        if not self._may_fail():
            self._may_parse_masking_key(data_in_bytes=data_in_bytes)
            self._parse_payload(data_in_bytes=data_in_bytes)
        else:
            raise InvalidMaskException
