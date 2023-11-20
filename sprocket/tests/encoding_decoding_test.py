import unittest
from sprocket import WebSocketFrameEncoder, WebsocketFrameDecoder


class TestWebSocketFrameEncoderDecoder(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create an instance of each class with default values for testing.
        """
        self.encoder = WebSocketFrameEncoder()
        self.decoder = WebsocketFrameDecoder()

    def test_init(self) -> None:
        # Frame encoder.
        self.assertEqual(self.encoder.MAX_FRAME_SIZE, 125)
        self.assertEqual(self.encoder.IS_MASKED, True)
        self.assertIsNotNone(self.encoder._frame_types)
        self.assertIsNotNone(self.encoder.mask_key_generator)

        # Frame decoder.
        self.assertEqual(self.decoder.status, True)

    def _decode_message(self, frames: list) -> str:
        data_in_bytes = b""
        final_message = ""

        for frame in frames:
            data_in_bytes = frame
            if not self._is_final_frame(data_in_bytes):
                # This is a fragmented frame
                self.decoder.decode_websocket_message(data_in_bytes=data_in_bytes)
                message_payload = self.decoder.payload_data
                final_message += message_payload.decode("utf-8")
            else:
                # This is a non-fragmented frame
                self.decoder.decode_websocket_message(data_in_bytes=data_in_bytes)
                message_payload = self.decoder.payload_data
                final_message += message_payload.decode("utf-8")

        if final_message and data_in_bytes:
            data_in_bytes = b""
            return final_message

    def _is_final_frame(self, data_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (data_in_bytes[0] & 0b10000000) >> 7 == 1

    def test_decoding(self) -> None:
        data = bytearray(b"0x81/0x05/0x48/0x65/0x6c/0x6c/0x6f")
        self.decoder.decode_websocket_message(data_in_bytes=data)
        # fin = self.decoder._fin
        # self.assertEqual(fin, 1)
        opcode = self.decoder.opcode
        self.assertEqual(opcode, 1)

    def test_generation_and_decoding(self) -> None:
        # Define payloads to be tested.
        payload_1 = "Hello"
        payload_2 = "Hello" * 12**4
        payload_3 = "{'json_data': 1}"

        # Encode payloads.
        data_1 = self.encoder.encode_payload_to_frames(payload=payload_1)
        data_2 = self.encoder.encode_payload_to_frames(payload=payload_2)
        data_3 = self.encoder.encode_payload_to_frames(payload=payload_3)

        decoded_data_1 = self._decode_message(frames=data_1)
        decoded_data_2 = self._decode_message(frames=data_2)
        decoded_data_3 = self._decode_message(frames=data_3)

        self.assertEqual(payload_1, decoded_data_1)
        self.assertEqual(payload_2, decoded_data_2)
        self.assertEqual(payload_3, decoded_data_3)
