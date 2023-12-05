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


import random, select, socket, threading, time, json, base64, secrets  # Import used libaries.
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    List,
    Literal,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for consoPORTBUFFER_SIZEle logging.
from .responsehandler import *
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..functions import check_port, check_frame_size  # Import used functions.
from ..exceptions import TCPPortException, FrameSizeException  # Import used exceptions.


__all__: Final[List[str]] = ["ClientSocketBaseImpl"]


class ClientSocketBaseImpl:  # rework with new frame encoder and websocketframe class updates + comments + sort layout
    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        TIMEOUT: Optional[int] = 5,
        MAX_FRAME_SIZE: Optional[int] = 125,
    ) -> None:
        if PORT is not None and not check_port(
            PORT=PORT  # Checks if provided value is valid.
        ):  # Checks if TCP_PORT is not none, if not then checks whether the provided value is valid.
            raise TCPPortException  # If value provided is not valid, raise ValueError
        else:
            # If no value provided, set _PORT to default value.
            self._PORT = PORT

        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not none, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.
        else:
            # Value not set in this class.
            pass

        self._WEBSOCKET_KEY = (
            self._generate_random_websocket_key()
        )  # Generate websocket key.
        self._HOST = HOST  # Set Host doamin.
        self._BUFFER_SIZE = BUFFER_SIZE  # Set buffer size (in bits).
        self._TIMEOUT = TIMEOUT  # Set select socket timeout.
        self._LOCK = threading.Lock()  # Set _LOCK.
        # ---------------------- #
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.
        self._socket_open = False  # Initialise _socket_open to open (True).
        self._frame_decoder = WebSocketFrameDecoder(
            status=True
        )  # Initialise _frame_decoder.
        self._frame_encoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=True
        )  # Initialise _frame_encoder.
        self._response_handler: HTTPResponseHandler = HTTPResponseHandler(
            WEBSOCKET_KEY=self._WEBSOCKET_KEY
        )

        self._setup_socket()  # Setup socket.

    @staticmethod
    def _generate_random_websocket_key() -> str:
        # Generate a 16 byte key.
        random_key = secrets.token_bytes(16)

        # Encode the random bytes to base64.
        base64_random_key = base64.b64encode(random_key).decode(
            "utf-8"
        )  # Decode with utf-8 as key is expeted to be a string.

        return base64_random_key

    def _setup_socket(self) -> None:
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.setblocking(True)

    def _close_socket(self) -> None:
        # Close the socket
        if self._socket_open:
            logger.warning("Closing socket")
            self._socket_open = False
            self._client_socket.close()
            return

    def _send_websocket_message(
        self,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        logger.debug("Sending Message")

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload, opcode=opcode
        )  # Encoded the given payload and opcode to WebSocket frame(s).

        for frame in frames:  # For each frame created.
            self._client_socket.send(frame)  # Send the frame to the server.

        return

    def _check_control_frame(self, opcode: bytes) -> None:
        if (
            opcode == FrameOpcodes.close
        ):  # Check if recieved frame opcode is a connection close opcode.
            self._close_socket()  # Close the socket connection.
            return
        if (
            opcode == FrameOpcodes.ping
        ):  # Check if recieved frame opcode is a ping opcode.
            logger.debug(f"Received Ping from Server.")
            self._pong()  # Send a pong frame in response.
            return
        if (
            opcode == FrameOpcodes.pong
        ):  # Check if recieved frame opcode is a pong opcode.
            logger.success(f"Received Pong from Server.")  #
            return

    def _pong(self) -> None:
        self._send_websocket_message(
            opcode=FrameOpcodes.pong
        )  # Send a pong frame using _send_websocket_message method.

    def _read_recv(
        self,
    ) -> Any | None:
        readable_sockets: list = select.select(
            [self._client_socket], [], [], self._TIMEOUT
        )[
            0
        ]  # Check if the socket is readable.

        if (
            self._client_socket not in readable_sockets
        ):  # If the socket is not readable.
            return None  # Return no data.

        with self._LOCK:  # Protect access to shared resources.
            retry_count: int = 0  # Initialise retry count.
            MAX_RETRIES: Literal[5] = 5  # Set MAX_RETRIES to 5.

            while (
                retry_count < MAX_RETRIES and self._client_socket in readable_sockets
            ):  # While the socket is readable and max retries has not been reached.
                data = self._client_socket.recv(
                    self._BUFFER_SIZE
                )  # Read data from the socket.

                if data:  # If there is data.
                    return data  # Return the data.
                else:  # If not.
                    retry_count += 1  # Update the retry_count
                    delay: int = (
                        0.1 * retry_count
                    ) ** 2  # Set exponentially increasing delay.
                    logger.warning(f"No data received, retrying in {delay} seconds...")
                    time.sleep(delay)  # Use delay.

            logger.critical("Max retries reached. Unable to read data.")

            return None  # Return no data.

    def _perform_websocket_handshake(self, retry_count: Optional[int] = 0) -> bool:
        retry_count = retry_count

        if retry_count >= 5:
            return False

        logger.debug("Performing WebSocket Handshake")

        # Create the handshake request and encode it (utf-8).
        handshake_request: bytes = (
            f"GET /websocket HTTP/1.1\r\n"
            f"Host: {self._HOST}:{self._PORT}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self._WEBSOCKET_KEY}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("utf-8")

        self._client_socket.send(
            handshake_request
        )  # Send the handshake request to the server.

        response: str = self._read_recv().decode("utf-8")  # Retrieve the response.

        if self._response_handler.validate_handshake_response(
            handshake_response=response
        ):
            logger.success("Connection to server complete.")

            self._trigger(event="connection", socket=self._client_socket)
            return True

        retry_count += 1

        self._perform_websocket_handshake(retry_count=retry_count)

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0x80) >> 7 == 1

    def _handle_message(self) -> None:
        frame_in_bytes: bytes = b""  # Initialise frame_in_bytes.
        final_message: str = ""  # Initialise final_message.

        while True:
            frame_data = self._read_recv()  # Read socket data.

            if frame_data == None:
                # Connection closed, or no data received.
                break

            logger.debug("Handling websocket message")

            frame_in_bytes = frame_data  # set frame_in_bytes to frame_data.

            if not self._is_final_frame(frame_in_bytes):
                # This is a fragmented frame
                self._frame_decoder.decode_websocket_message(
                    frame_in_bytes=frame_in_bytes
                )  # Decode the given frame.

                message_payload = self._frame_decoder.payload_data.decode(
                    "utf-8"
                )  # Retrieve the decoded payload_data.

                final_message += (
                    message_payload  # Add the decoded message to the final message.
                )
            else:
                # This is a non-fragmented frame
                self._frame_decoder.decode_websocket_message(
                    frame_in_bytes=frame_in_bytes
                )  # Decode the frame.

                control_opcode = (
                    self._frame_decoder.opcode
                )  # Retrieve the opcode (control frames can't be fragmented).

                self._check_control_frame(
                    opcode=control_opcode
                )  # Check which opcode is present.

                message_payload = self._frame_decoder.payload_data.decode(
                    "utf-8"
                )  # Retrieve the decoded payload_data.

                final_message += (
                    message_payload  # Add the decoded message to the final message.
                )
                break  # Break the loop early so no more data is read for this message.

        if (
            final_message and frame_in_bytes
        ):  # If both the final message and frame are present.
            frame_in_bytes = b""  # Reset the frame_in_bytes.

            message_dict: dict = json.loads(
                final_message
            )  # Load the final message (always a dictionary).

            self._trigger_event_from_message(
                final_message=message_dict
            )  # Trigger the event given.

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        if event in self._event_handlers:  # If the event is in _event_handlers.
            for handler in self._event_handlers[
                event
            ]:  # For each handler asinged to the event.
                handler(
                    *args,
                    **kwargs,  # Provide required positional arguments and key arguments.
                )  # Call the handler.

    def _trigger_event_from_message(self, final_message: dict) -> None:
        final_message_keys = list(
            final_message.keys()
        )  # Extract the keys from the final message.

        event = final_message_keys[
            0
        ]  # Extract the event key (will always be first key).

        if not event:  # If no event was given.
            logger.warning(
                f"Message with no endpoint recieved: {final_message}"
            )  # Log the error, no execption is needed here.
            return

        self._trigger(event, final_message[event])  # Trigger the event given.

        return

    def _listen_for_messages(self) -> None:
        while self._socket_open:
            self._handle_message()
