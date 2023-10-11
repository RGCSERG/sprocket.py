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

from typing import Final, List


__all__: Final[List[str]] = ["WebsocketFrame"]


class WebsocketFrame:
    """Python class that represents a simple WebSocket frame.
    Provides methods for parsing WebSocket frame messages,
    extracting its components, and returning the payload data."""

    def __init__(self):
        self._fin = 0
        self._rsv1 = 0
        self._rsv2 = 0
        self._rsv3 = 0
        self._opcode = 0
        self._mask = 0
        self._payload_length = 0
        self._mask_key = None
        self._payload_data = b""

    def populateFromWebsocketFrameMessage(self, data_in_bytes):
        self._parse_flags(data_in_bytes)
        self._parse_payload_length(data_in_bytes)
        self._maybe_parse_masking_key(data_in_bytes)
        self._parse_payload(data_in_bytes)

    def _parse_flags(self, data_in_bytes):
        first_byte = data_in_bytes[0]
        self._fin = (first_byte & 0b10000000) >> 7
        self._rsv1 = (first_byte & 0b01000000) >> 6
        self._rsv2 = (first_byte & 0b00100000) >> 5
        self._rsv3 = (first_byte & 0b00010000) >> 4
        self._opcode = first_byte & 0b00001111

        second_byte = data_in_bytes[1]
        self._mask = (second_byte & 0b10000000) >> 7

    def _parse_payload_length(self, data_in_bytes):
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

    def _maybe_parse_masking_key(self, data_in_bytes):
        if self._mask:
            self._mask_key = data_in_bytes[
                self._mask_key_start : self._mask_key_start + 4
            ]

    def _parse_payload(self, data_in_bytes):
        payload_data = b""
        if self._payload_length > 0:
            payload_start = (
                self._mask_key_start if self._mask else self._mask_key_start - 4
            )
            encoded_payload = data_in_bytes[
                payload_start : payload_start + self._payload_length
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

    def get_payload_data(self):
        return self._payload_data
