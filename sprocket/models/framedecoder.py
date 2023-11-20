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


from typing import Final, List, Literal, Optional
from .maskkey import *
from ..exceptions import *


"""
All comments refering to binary operations will assume the structure of a btye to be as such;

0b  1   1   1   1   1   1   1   1 # Binary value
0b  8th 7th 6th 5th 4th 3rd 2nd 1st # Position
0b  128 64  32  16  8   4   2   1 # Denary value
"""


__all__: Final[List[str]] = ["WebsocketFrameDecoder"]


class WebsocketFrameDecoder:  # inherit from descriptor class + comments
    """Python class that represents a simple WebSocket frame.
    Provides methods for parsing WebSocket frame messages,
    extracting its components, and returning the payload data."""

    def __init__(self, status: Optional[bool] = True) -> None:
        """
        Initialises the individual parts of the websocket frame,
        where status defines weather the machine running the code is either a client or remote host.

        Args:
            status bool: determines weather a machine is a client or remote host,
            defaults to a client (true), server = false.
        """

        self.status = status  # Status, defining machines type.

        self._fin: int = 0  # Fin bit.
        self._rsv1: int = 0  # Rsv1 bit.
        self._rsv2: int = 0  # Rsv2 bit.
        self._rsv3: int = 0  # Rsv3 bit.
        self._opcode: int = 0  # Frame's Opcode.
        self._mask: int = 0  # Mask bit (1/0 for true/false respectively).
        self._payload_length: bytes = 0  # Payload length.
        self._mask_key: bytearray = None  # Mask key (if masked), for decoding.
        self._payload_data: bytes = b""  # Actualy decoded payload (in bytes).

    @property
    def payload_data(self) -> bytes:
        """
        Property Method for retrieving private attribute _payload_data,
        used by <instance>.<property> .

        Returns:
            _payload_data bytes: Payload data of the frame given.
        """

        return self._payload_data

    @property
    def opcode(self) -> int:
        """
        Property Method for retrieving private attribute _opcode,
        used by <instance>.<property> .

        Returns:
            _opcode int: Opcode in integer form of the frame.
        """

        return self._opcode

    @staticmethod
    def _parse_fin_bit(first_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the fin bit from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            first_byte bytes: First byte of the frame.

        Returns:
            fin int: The most significant (8th) bit (fin bit) of the frame.
        """

        fin = (
            first_byte  # Perform AND operator (&) with operand 0x80 (binary: 10000000, denary: 128) on the first byte,
            & 0x80  # This isolates the fin bit, by only giving a successful and operation for the 8th bit.
        ) >> 7  # Then Right-shift (>>) the result by 7 positions moves the isolated bit to the 1st position (least significant bit).
        return fin

    @staticmethod
    def _parse_rsv1_bit(first_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the rsv1 bit from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            first_byte bytes: First byte of the frame.

        Returns:
            rsv1 int: The 7th bit (rsv1 bit) of the frame.
        """

        rsv1 = (
            first_byte  # Perform AND operator (&) with operand 0x40 (binary: 01000000, denary: 64) on the first byte,
            & 0x40  # This isolates the rsv1 bit, by only giving a successful and operation for the 7th bit.
        ) >> 6  # Then Right-shift (>>) the result by 6 positions moves the isolated bit to the 1st position (least significant bit).
        return rsv1

    @staticmethod
    def _parse_rsv2_bit(first_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the rsv2 bit from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            first_byte bytes: First byte of the frame.

        Returns:
            rsv2 int: The 6th bit (rsv2 bit) of the frame.
        """

        rsv2 = (
            first_byte  # Perform AND operator (&) with operand 0x20 (binary: 00100000, denary: 32) on the first byte,
            & 0x20  # This isolates the rsv2 bit, by only giving a successful and operation for the 6th bit.
        ) >> 5  # Then Right-shift (>>) the result by 5 positions moves the isolated bit to the 1st position (least significant bit).
        return rsv2

    @staticmethod
    def _parse_rsv3_bit(first_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the rsv3 bit from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            first_byte bytes: First byte of the frame.

        Returns:
            rsv3 int: The 5th bit (rsv3 bit) of the frame.
        """

        rsv3 = (
            first_byte  # Perform AND operator (&) with operand 0x10 (binary: 00010000, denary: 16) on the first byte,
            & 0x10  # This isolates the rsv3 bit, by only giving a successful and operation for the 5th bit.
        ) >> 4  # Then Right-shift (>>) the result by 4 positions moves the isolated bit to the 1st position (least significant bit).
        return rsv3

    @staticmethod
    def _parse_opcode(first_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the opcode from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            first_byte bytes: First byte of the frame.

        Returns:
            opcode int: The second half (4th - 1st) of the first byte (opcode) of the frame, in integer form.
        """

        opcode = (
            first_byte  # Perform AND operator (&) with operand 0xF (binary: 00001111, denary: 15) on the first byte,
            & 0xF  # This isolates the opcode, by only giving a successful and operation for the second half of the first byte.
        )  # This does not require Right-shifting as the result is already in least significant position it can be in.
        return opcode

    @staticmethod
    def _parse_mask(second_byte: bytes) -> int:
        """
        Static method used to retrieve (parse) the mask bit from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            second_byte bytes: Second byte of the frame.

        Returns:
            mask int: The most significant (8th) bit (mask bit) of the second byte, of the frame.
        """

        mask = (
            second_byte  # Perform AND operator (&) with operand 0x80 (binary: 10000000, denary: 128) on the second byte,
            & 0x80  # This isolates the mask bit, by only giving a successful and operation for the 8th bit.
        ) >> 7  # Then Right-shift (>>) the result by 7 positions moves the isolated bit to the 1st position (least significant bit).
        return mask

    @staticmethod
    def _parse_payload_length(
        data_in_bytes: bytearray,
    ) -> tuple[int, Literal[10, 4, 2]]:
        """
        Static method used to retrieve (parse) the payload length from any given frame.

        This method is static as it does not rely of the instance of the class.

        Args:
            data_in_bytes bytearray: Whole frame in the form of an bytearray.

        Returns:
            tuple[
                payload_length int: Length of the payload in integer form.
                start_mask_key Literal[10, 4, 2]: Start of the masking key (if masked), within the frame.
            ]
        """

        payload_length = (
            data_in_bytes[
                1
            ]  # Perform AND operator (&) with operand 0x7F (binary: 01111111, denary: 127) on the second byte,
            & 0x7F  # This isolates the payload length from the mask bit, by enforcing a failed operation for the 8th bit.
        )  # This does not require Right-shifting as the result is already in least significant position it can be in.
        start_mask_key = 2  # Set start_mask_key to default position (3rd byte).

        if (
            payload_length == 0x7E
        ):  # If payload length is equal to 0x7E (126), then the payload length is stored as a 16 bit unsigned integer, over the next two bytes (bytes 3 and 4).
            payload_length = int.from_bytes(
                data_in_bytes[2:4], byteorder="big"
            )  # Retrieve payload from bytes 3 and 4.
            start_mask_key = 4  # Move the start of the masking key back 2 bytes (byte 5), to account for the extended payload length.
        if (
            payload_length == 0x7F
        ):  # If payload length is equal to 0x7F (127), then the paylood length is stored as a 64 bit unsigned integer, over the next 8 bytes (bytes 3-10).
            payload_length = int.from_bytes(
                data_in_bytes[2:10], byteorder="big"
            )  # Retrieve payload from bytes 3-10.
            start_mask_key = 10  # Move the start of the masking key back 8 bytes (byte 11), to account for the extended payload length.

        return payload_length, start_mask_key

    def _parse_websocket_frame_header(self, data_in_bytes: bytearray) -> None:
        """
        Instance Method to parse all parts of the websocket frame which are follow the same process, for each instance.

        Args:
            data_in_bytes bytearray: Whole frame in the form of an bytearray.
        """

        first_byte = data_in_bytes[0]  # Set first_byte.
        second_byte = data_in_bytes[1]  # Set second_byte.

        self._fin = self._parse_fin_bit(first_byte=first_byte)  # Parse fin bit.
        self._rsv1 = self._parse_rsv1_bit(first_byte=first_byte)  # Parse rsv1 bit.
        self._rsv2 = self._parse_rsv2_bit(first_byte=first_byte)  # Parse rsv2 bit.
        self._rsv3 = self._parse_rsv3_bit(first_byte=first_byte)  # Parse rsv3 bit.
        self._opcode = self._parse_opcode(first_byte=first_byte)  # Parse opcode.
        self._mask = self._parse_mask(second_byte=second_byte)  # Parse mask bit.
        self._payload_length, self._start_mask_key = self._parse_payload_length(
            data_in_bytes=data_in_bytes
        )  # Parse payload length and set start of mask key.

    def _may_parse_masking_key(self, data_in_bytes: bytearray) -> None:
        """
        Parses masking key, using the value for the start of the masking key, determined when parsing the payload length.
        """

        if self._mask:  # If the frame's mask bit is True.
            self._mask_key = data_in_bytes[
                self._start_mask_key : self._start_mask_key
                + 4  # Masking key is 4 bytes long, so add four to mark the end of the masking key.
            ]  # Retrieve masking key.

    def _parse_payload(self, data_in_bytes: bytearray) -> None:
        """
        Parses the payload, using values determined in previously called functions.

        Args:
            data_in_bytes bytearray: Whole frame in the form of an bytearray.
        """

        payload_data = b""  # Initialise payload_data as a empty bytes.
        if (
            self._payload_length
        ):  # For efficiancy, this checks weather there is anything to retrieve.
            payload_start = (
                self._start_mask_key + 4
                if self._mask
                else self._start_mask_key  # Checks if the message is masked, setting payload start accordingly.
            )
            encoded_payload = data_in_bytes[
                payload_start : payload_start + self._payload_length
            ]  # Retrieves payload.

            if self._mask:  # If the payload is masked, it must be decoded.
                MaskKey.unmask_payload(
                    encoded_payload=encoded_payload,
                    mask_key=self._mask_key,
                )  # Decode payload (abstracted by other class).
            else:  # If payload is not masked, it doesn't need to be decoded.
                payload_data = encoded_payload

        self._payload_data = payload_data

    def _may_fail(self) -> bool:
        """
        Checks if the message recived is in the right format, for the given device role.

        As in accordance with RFC6455, messages recieved must be masked / unmasked,
        depending on whether a machine is a remote-host / client respectively.

        Returns:
            bool: True / False for error / no error respectively.
        """

        if (
            self._mask == self.status
        ):  # Both the mask and the status of the machine cannot be equal, if they are an error has occured.
            return True
        return False

    def decode_websocket_message(self, data_in_bytes: bytes) -> None:
        """
        Populates the frame instance with data,
        parsed using class methods.
        """
        self._parse_websocket_frame_header(
            data_in_bytes=data_in_bytes
        )  # Parses header data.
        if (
            not self._may_fail()
        ):  # For efficiancy reasons, the class will not process the rest of the data if an error has occured.
            self._may_parse_masking_key(
                data_in_bytes=data_in_bytes
            )  # MAY parse masking key (if messages is masked).
            self._parse_payload(data_in_bytes=data_in_bytes)  # Parses payload.
        else:
            raise InvalidMaskException  # If an error has occured raise InvalidMaskException.
