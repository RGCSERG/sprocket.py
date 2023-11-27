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


class MaskKey:
    """Used for all Mask Key related opertaions"""

    @staticmethod
    def random(seed: int) -> int:
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        return (seed >> 24) & 0xFF

    def generate_masking_key(self, seed: Optional[int] = 1234) -> bytearray:
        """
        Generates masking key.

        Args:
            seed optional int: Seed to create masking key with.

        Returns:
            masking_key bytearray: Generated masking key.
        """
        masking_key: bytearray = bytearray(
            self.random(seed=seed if seed else 1234) for _ in range(4)
        )  # Generate masking key.
        return masking_key

    @staticmethod
    def mask_payload(payload: bytes, mask_key: bytearray, payload_length: int) -> bytes:
        """
        Takes in a payload and mask_key as arguments and masks the payload with respect to the mask_key.

        Args:
            payload bytes: Payload to be masked.
            mask_key bytearray: Mask key to be used.

        Returns:
            masked_payload bytes: The resultant masked payload.
        """

        masked_payload: bytes = bytes(
            payload[i]
            ^ mask_key[
                i % 4
            ]  # Returns sequence of 0, 1, 2, 3 indefinitely, so that the length of the mask_key cannot be exceeded.
            for i in range(
                payload_length
            )  # For every byte in the payload, mask it with the corresponding mask key index.
        )

        return masked_payload

    @staticmethod
    def unmask_payload(masked_payload: bytearray, mask_key: bytearray) -> bytes:
        """
        Takes in a masked_payload, and mask_key as arguments and unmasks the payload.

        Args:
            masked_payload bytearray: Payload to be unmasked.
            mask_key bytearray: Mask key to unmask the payload with.

        Returns:
            payload_data bytes: The unmasked payload data.
        """

        unmasked_payload: list[int] = [
            byte
            ^ mask_key[
                i % 4
            ]  # Returns sequence of 0, 1, 2, 3 indefinitely, so that the length of the mask_key cannot be exceeded.
            for i, byte in enumerate(
                masked_payload
            )  # For every byte in the payload, mask it with the corresponding mask key index.
        ]

        payload_data: bytes = bytes(unmasked_payload)  # Store unmaksed payload.
        return payload_data
