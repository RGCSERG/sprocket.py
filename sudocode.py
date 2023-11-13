from abc import ABC, abstractmethod
from typing import List, Optional


class WebSocketFrameEncoder(ABC):
    def __init__(
        self, max_frame_size: optional integer default = 125, is_masked: optional boolean default = True
    ) -> None:
        """
        Initializes the maximum frame size and masking parameters (is_masked determined whether user is client or remote host).

        self.max_frame_size = max_frame_size
        self.mask_key_generator = CustomRandomGenerator()
        self.is_masked = is_masked

        Args:
            max_frame_size optional integer
            is_masked optional boolean
        """

    @abstractmethod
    def generate_frame(self, payload: optional bytes default = b"", opcode: optional bytes default = 0x1, fin: optional bytes default = 0x1
    ) -> WSFrame:
        """generate_frame will be the private method which will convert given data into a binary WSFrame

        frame = instance of empty byte array
        payload_length = length of payload

        Args:
            payload optional bytes
            opcode optional bytes
            fin(bit) optional bytes
        
        Returns:
            WSFrame
        """
    
        if payload_length <= 125:
            """For small payloads, use a 7-bit payload length representation.
            Append opcode and fin with proper bit manipulation.
            If masked, append the masking flag and payload length.
            Generate a masking key and apply masking to payload if needed.
            Append the masked payload or the original payload accordingly."""
        elif payload_length <= 0xFFFF:
            """For medium-sized payloads, use a 16-bit payload length representation.
            Append opcode and fin with proper bit manipulation.
            If masked, append the masking flag and payload length.
            Generate a masking key and apply masking to payload if needed.
            Append the masked payload or the original payload accordingly."""
        else:
            """For large payloads, use a 64-bit payload length representation.
            Append opcode and fin with proper bit manipulation.
            If masked, append the masking flag and payload length.
            Generate a masking key and apply masking to payload if needed.
            Append the masked payload or the original payload accordingly."""

    @abstractmethod
    def encode_payload_to_frames(self, payload: optional string defualt = "", opcode: optional bytes defualt = 0x1
    ) -> List[WSFrames]:
        """Encodes a payload into a list of WebSocket frame(s) (WSFrame) using private method generate_frame

        Encode payload into UTF-8 and determine payload length.
        Initialize an empty list to store frames.

        Args:
            payload optional string
            opcode

        Returns:
            list of created WSFrame(s)
        """

        if payload_length <= self.max_frame_size:
            """If payload fits within the maximum frame size, create a single frame.
            Append the generated frame to the list."""
        else:
            """If payload exceeds the maximum frame size, split it into multiple frames.
            Iterate over payload chunks and create frames accordingly.
            Append each frame to the list."""
