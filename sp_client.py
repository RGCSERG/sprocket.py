from sprocket import ClientSocketImpl

client = ClientSocketImpl()

if __name__ == "__main__":
    client.start_websocket_client()

# from test import *
# from test import WebSocketBaseImpl

# frame_encoder = WebSocketFrameEncoder()


# data = frame_encoder.encode_payload_to_frames("123456789")


# # Given binary data
# for index, frame in enumerate(data):
#     binary_data = frame

#     # Convert each byte to its binary representation and concatenate them
#     binary_string = "".join(format(byte, "08b") for byte in binary_data)

#     print(f"Frame {index + 1}: {binary_string}")


# framethingy = WebSocketBaseImpl()

# framethingy._handle_websocket_message(data)

# # 1000000110001011101101100011010010111111010110001000011100000110100011000110110010000011000000101000100001100000100011110000010110001111
# # 0011000100110010001100110011010000110101001101100011011100111000001110010011000100110000
