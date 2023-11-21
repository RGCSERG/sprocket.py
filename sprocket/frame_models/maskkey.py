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


__all__: Final[List[str]] = ["MaskKey"]


class MaskKey:  # comments + make inherit from descriptor class
    @staticmethod
    def mask_payload(payload: bytes, mask_key: bytearray, payload_length: int) -> bytes:
        masked_payload: bytes = bytes(
            payload[i] ^ mask_key[i % 4] for i in range(payload_length)
        )

        return masked_payload

    @staticmethod
    def unmask_payload(encoded_payload: bytearray, mask_key: bytearray) -> bytes:
        unmasked_payload: list[int] = [
            byte ^ mask_key[i % 4] for i, byte in enumerate(encoded_payload)
        ]

        payload_data = bytes(unmasked_payload)
        return payload_data

    @staticmethod
    def random(seed: int) -> int:
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        return (seed >> 24) & 0xFF

    def generate_masking_key(self, seed: Optional[int] = 1234) -> bytearray:
        masking_key: bytearray = bytearray(self.random(seed=seed) for _ in range(4))
        return masking_key
