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


import random, select, socket, threading, time, json  # Import used libaries.
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
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..sockets import ClientSocket  # Import Abstract model.
from ..functions import check_port, check_frame_size  # Import used functions.
from ..exceptions import TCPPortException, FrameSizeException  # Import used exceptions.


__all__: Final[List[str]] = ["ClientSocketBaseImpl"]


class ClientSocketBaseImpl(
    ClientSocket
):  # rework with new frame encoder and websocketframe class updates + comments + sort layout
    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        TIMEOUT: Optional[int] = 5,
        MAX_FRAME_SIZE: Optional[int] = 125,
    ) -> None:
        # Constructor Method
        if PORT is not None and not check_port(
            PORT=PORT  # Checks if provided value is valid.
        ):  # Checks if PORT is not none, if not then checks whether the provided value is valid.
            raise TCPPortException  # If value provided is not valid, raise ValueError
        else:
            # If no value provided, set _PORT to default value
            self._PORT = PORT

        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not none, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.
        else:
            # value not set in this class
            pass

        self._TCP_KEY = self._generate_random_websocket_key()  # Generate websocket key.
        self._HOST = HOST  # Set _HOST.
        self._BUFFER_SIZE = BUFFER_SIZE  # Set _BUFFER_SIZE.
        self._TIMEOUT = TIMEOUT  # Set _TIMEOUT.
        # ---------------------- #
        self._LOCK = threading.Lock()  # Set _LOCK.
        self._socket_open = False  # Set _socket_open.
        self._frame_decoder = WebSocketFrameDecoder(status=True)  # Set _frame_decoder.
        self._frame_encoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=True  # Set _frame_encoder.
        )
        self._frame_types = FrameOpcodes()  # Set _frame_types.
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.

        self._setup_socket()  # Setup socket.

    # Private methods

    def _check_control_frame(self, opcode: bytes) -> None:
        # Handle control frames
        if (
            opcode == self._frame_types.close
        ):  # Check if recieved frame opcode is a connection close opcode.
            self._close_socket()  # Close the socket connection.
            return
        if (
            opcode == self._frame_types.ping
        ):  # Check if recieved frame opcode is a ping opcode.
            logger.debug(f"Received Ping from Server.")
            self._pong()  # Send a pong frame in response.
            return
        if (
            opcode == self._frame_types.pong
        ):  # Check if recieved frame opcode is a pong opcode.
            logger.success(f"Received Pong from Server.")  #
            return

    def _pong(self) -> None:
        # Send Pong response
        self._send_websocket_message(
            opcode=self._frame_types.pong
        )  # Send a pong frame using _send_websocket_message method.

    def _send_websocket_message(
        self,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Send a WebSocket message to the server.

        Args:
            message Optional[str]: The message to send.
            event Optional[str]: The event name associated with the message.
            opcode Optional[bytes]: The opcode indicating the type of message.
        """
        if self._socket_open:
            logger.debug("Sending Message")

            frames = self._frame_encoder.encode_payload_to_frames(
                payload=payload, opcode=opcode
            )

            for frame in frames:
                self._client_socket.send(frame)

    def _handle_websocket_message(self) -> None:
        # Handle incoming WebSocket messages
        frame_in_bytes: bytes = b""  # Initialise frame_in_bytes.
        final_message: str = ""  # Initialise final_message.

        while True:  # While data is being sent.
            frame_data = self._read_recv()
            if not frame_data:
                # Connection closed, or no data received.
                break

            logger.debug("Handling WebSocket message")

            frame_in_bytes = frame_data
            if not self._is_final_frame(frame_in_bytes):
                # This is a fragmented frame
                self._frame_decoder.decode_websocket_message(
                    frame_in_bytes=frame_in_bytes
                )
                message_payload = self._frame_decoder.payload_data.decode("utf-8")
                final_message += message_payload
            else:
                # This is a non-fragmented frame
                self._frame_decoder.decode_websocket_message(
                    frame_in_bytes=frame_in_bytes
                )
                control_opcode = self._frame_decoder.opcode
                self._check_control_frame(opcode=control_opcode)
                message_payload = self._frame_decoder.payload_data.decode("utf-8")
                final_message += message_payload
                break

        if final_message and frame_in_bytes:
            frame_in_bytes = b""
            message_dict: dict = json.loads(final_message)

            self._trigger_event_from_message(final_message=message_dict)

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        # Trigger event handlers
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args, **kwargs)

    def _trigger_event_from_message(self, final_message: dict) -> None:
        final_message_keys = list(final_message.keys())

        event = final_message_keys[0]

        if not event:
            logger.warning(f'Message with no endpoint recieved: {final_message[""]}')
            return

        self._trigger(event, final_message[event])

        return

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0x80) >> 7 == 1

    def _close_socket(self) -> None:
        # Close the socket
        if self._socket_open:
            logger.warning("Closing socket")
            self._socket_open = False
            self._client_socket.close()
            return

    def _read_recv(self) -> None:
        # Read data from the socket
        readable_sockets = select.select([self._client_socket], [], [], self._TIMEOUT)[
            0
        ]

        if self._client_socket not in readable_sockets:
            return None

        with self._LOCK:
            retry_count: int = 0
            MAX_RETRIES: Literal[5] = 5

            while retry_count < MAX_RETRIES and self._client_socket in readable_sockets:
                data = self._client_socket.recv(self._BUFFER_SIZE)
                if data:
                    return data
                else:
                    retry_count += 1
                    delay: int = (0.1 * retry_count) ** 2
                    logger.warning(f"No data received, retrying in {delay} seconds...")
                    time.sleep(delay)

            logger.critical("Max retries reached. Unable to read data.")
            return None

    def _perform_websocket_handshake(self) -> bool:
        # Perform WebSocket handshake
        logger.debug("Performing WebSocket Handshake")

        request = (
            f"GET /websocket HTTP/1.1\r\n"
            f"Host: {self._HOST}:{self._PORT}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self._TCP_KEY}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )

        self._client_socket.send(request.encode("utf-8"))

        response = self._read_recv().decode("utf-8")
        if "101 Switching Protocols" in response:
            self._trigger(event="connection", socket=self._client_socket)
            return True
        else:
            return False

    @staticmethod
    def _generate_random_websocket_key() -> str:
        # Generate a random WebSocket key
        characters = "0123456789ABCDEF"
        random_key = "".join(random.choice(characters) for _ in range(32))
        return random_key

    def _setup_socket(self) -> None:
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.setblocking(True)

    def _listen_for_messages(self) -> None:
        while self._socket_open:
            self._handle_websocket_message()
