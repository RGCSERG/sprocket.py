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

from typing import Final, List, Optional  # Used for type annotations and decloration.
from .maskkey import *  # Import used classes.
from .frameopcodes import *  # Import used classes.

__all__: Final[List[str]] = ["WebSocketFrameEncoder"]


class WebSocketFrameEncoder:  # make inherit from descriptor class + tests + rework?
    def __init__(
        self,
        MAX_FRAME_SIZE: Optional[
            int
        ] = 125,  # Defaults to 125 (maximum control frame size as stated in RFC6455)
        IS_MASKED: Optional[bool] = True,  # Defaults to True (client).
    ) -> None:
        """
        Initialises the maximum frame size and masking parameters.
        Generates random mask key using MaskKey class.

        Args:
            MAX_FRAME_SIZE integer: determines what the maximum frame size created should be.
            IS_MASKED boolean: determined by whether machine is client or remote host, resulting in true, false respectivly,
            (in accordance with RFC6455 5.1).
        """
        self.MAX_FRAME_SIZE = MAX_FRAME_SIZE  # set MAX_FRAME_SIZE.
        self.IS_MASKED = IS_MASKED  # set IS_MASKED.

        self.mask_key_generator = (
            MaskKey()
        )  # Initialise an instance of the MaskKey under mask_key_generator (Composition).

    def _generate_frame(
        self,
        payload: Optional[
            bytes
        ] = b"",  # Defaults to emtpy bytes string (so that empty control frames do not requre a paylaod).
        opcode: Optional[
            bytes
        ] = 0x1,  # Defaults to a text frame (0x1 denotes hexidecimal format of opcode of 0001).
        fin: Optional[
            bytes
        ] = 0x1,  # Defaults to final frame (if a fin bit is not produced then the program will asume it is the final frame).
    ) -> bytearray:
        """
        Private method designed generate a single WebSocket frame, converts given bytes data into a valid WebSocket Frame.

        Args:
            payload bytes: the given payload to be serialised into acceptable WebSocket format
            opcode bytes: opcode to be inserted into the frame.
            fin bytes: determines fin bit (whether or not frame created is final), to be inserted into frame.

        """

        frame = bytearray()  # Initialises frame variable as a bytearray.
        payload_length = len(
            payload
        )  # Sets the length of the payload to be serialised.

        if (
            payload_length <= 0x7D
        ):  # For standard payloads with length <= 0x7D (125), use a 7-bit payload length representation.
            frame.append(
                (fin << 0x7) | opcode
            )  # Append opcode and fin, with proper bit manipulation. (1)
            frame.append(
                (self.IS_MASKED << 0x7) | payload_length
            )  # Append the masking flag and payload length, with proper bit manipulation. (2)

            if self.IS_MASKED:
                mask_key = (
                    self.mask_key_generator.generate_masking_key()
                )  # If masked (client message), generate a masking key. (3)
                frame.extend(
                    mask_key
                )  # Append masking key to the end of the frame. (4)
                masked_payload = MaskKey.mask_payload(
                    payload=payload, mask_key=mask_key, payload_length=payload_length
                )  # Perform masking operation on the payload. (5)
                frame.extend(
                    masked_payload
                )  # Append masked payload to the end of the frame. (6)
            else:
                frame.extend(
                    payload
                )  # Append non masked payload to the end of the frame. (7)
        elif (
            payload_length <= 0xFFFF
        ):  # payload length that is less than or equal to 0xFFFF (65535).
            # For payloads with length <= 0xFFFF, use a 16-bit payload length representation.
            frame.append(
                (fin << 0x7) | opcode
            )  # Append opcode and fin with proper bit manipulation. (1)
            frame.append(
                (self.IS_MASKED << 0x7) | 0x7E
            )  # Append the masking flag and payload length, with proper bit manipulation. (2)
            frame.extend(
                payload_length.to_bytes(2, byteorder="big")
            )  # Append the masking flag and payload length, with proper bit manipulation. (2)
            if self.IS_MASKED:
                mask_key = (
                    self.mask_key_generator.generate_masking_key()
                )  # If masked (client message), generate a masking key. (3)
                frame.extend(
                    mask_key
                )  # Append masking key to the end of the frame. (4)
                masked_payload = MaskKey.mask_payload(
                    payload=payload, mask_key=mask_key, payload_length=payload_length
                )  # Perform masking operation on the payload. (5)
                frame.extend(
                    masked_payload
                )  # Append masked payload to the end of the frame. (6)
            else:
                frame.extend(
                    payload
                )  # Append non masked payload to the end of the frame. (7)
        else:
            # payload length is greater length than 0xFFFF (65535).
            # For payloads with  length > 0xFFFF (65535) , use a 64-bit payload length representation.
            frame.append(
                (fin << 0x7) | opcode
            )  # Append opcode and fin with proper bit manipulation. (1)
            frame.append(
                (self.IS_MASKED << 0x7) | 0x7F
            )  # Append the masking flag and payload length, with proper bit manipulation. (2)
            frame.extend(
                payload_length.to_bytes(8, byteorder="big")
            )  # Append the masking flag and payload length, with proper bit manipulation. (2)
            if self.IS_MASKED:
                mask_key = (
                    self.mask_key_generator.generate_masking_key()
                )  # If masked (client message), generate a masking key. (3)
                frame.extend(
                    mask_key
                )  # Append masking key to the end of the frame. (4)
                masked_payload = MaskKey.mask_payload(
                    payload=payload, mask_key=mask_key, payload_length=payload_length
                )  # Perform masking operation on the payload. (5)
                frame.extend(
                    masked_payload
                )  # Append masked payload to the end of the frame. (6)
            else:
                frame.extend(
                    payload
                )  # Append non masked payload to the end of the frame. (7)

        return frame

    def _is_last_created_frame(self, i: int) -> bytes:
        """
        Checks if the frame to be created is the final frame, and returns corresponding value.

        Args:
            i int: count which is being iterated over

        Returns:
            0x0 if a continuation frame, and 0x1 if final frame of message,
            (0x0 denoting continuation frame as stated in RFC6455 5.2).
        """
        return (
            FrameOpcodes.continuation
            if (i + self.MAX_FRAME_SIZE) < self.payload_length
            else FrameOpcodes.text
        )

    def encode_payload_to_frames(
        self, payload: Optional[str] = "", opcode: Optional[bytes] = 0x1
    ) -> list:
        """
        Encodes a payload into a list of WebSocket frame(s) using private method _generate_frame.

        Args:
            payload str: payload to be serialised
            opcode: allows control frames to be sent,
            (doesn't conflict with messages longer than max frame size,
            as control frames are required to fit a singular frame).

        Returns:
            list of created WebSocket Frame(s)
        """

        self.payload = payload.encode("utf-8")  # Encode payload into UTF-8.
        self.payload_length = len(self.payload)  # Determine payload length.
        frames = []  # Initialises an empty list to store frames created.

        if self.payload_length <= self.MAX_FRAME_SIZE:
            """
            If payload fits within the maximum frame size, create a single frame.
            Append the generated frame to the list.
            """
            frames.append(
                self._generate_frame(payload=self.payload, opcode=opcode, fin=0x1)
            )  # Creates frame and then appends it to the frames list.
        else:
            """
            If payload exceeds the maximum frame size, split it into multiple frames.
            Iterates over payload chunks and create frames accordingly, then append each frame to the list.
            """
            for i in range(0, self.payload_length, self.MAX_FRAME_SIZE):
                frame_payload = self.payload[
                    i : i + self.MAX_FRAME_SIZE
                ]  # Selects chunk to be serialised.
                fin = self._is_last_created_frame(i)  # Asigns fin bit value.
                opcode = self._is_last_created_frame(i)  # Asigns opcode bit value.
                frames.append(
                    self._generate_frame(frame_payload, opcode, fin)
                )  # Creates frame and then appends it to the frames list.

        return frames
