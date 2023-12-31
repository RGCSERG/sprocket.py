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


import select, socket, threading, json, time  # Import used libaries.
from typing import (
    Any,
    Callable,
    Final,
    List,
    Dict,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for console logging.
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..functions import check_frame_size, check_if_control  # Import used functions.
from ..exceptions import FrameSizeException  # Import used exceptions.

__all__: Final[List[str]] = ["SprocketSocketBase"]


class SprocketSocketBase:
    def __init__(
        self,
        SOCKET: socket,
        PARENT_SERVER,
        MAX_FRAME_SIZE: Optional[int] = 125,
        BUFFER_SIZE: Optional[int] = 8192,
    ) -> None:
        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not None, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.

        self.SOCKET: socket = SOCKET
        self._PARENT_SERVER = PARENT_SERVER
        self._BUFFER_SIZE: int = BUFFER_SIZE  # Set sockets backlog.
        self._LOCK = threading.Lock()  # Protect access to shared resources.
        # ---------------------- #
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.
        self._joined_rooms: set = set()
        self._status = True
        self._frame_decoder: WebSocketFrameDecoder = WebSocketFrameDecoder(
            status=False
        )  # Initialise _frame_decoder.
        self._frame_encoder: WebSocketFrameEncoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=False
        )  # Initialise _frame_encoder.

    def _close_socket(self, critical: Optional[bool]) -> None:
        self._PARENT_SERVER._close_socket(socket=self, critical=critical)

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
            with self._LOCK:
                self.SOCKET.send(frame)  # Send the frame to the client.

        return

    def _ping(self) -> None:
        if not self._status:
            self.close()
            return

        if self in self._PARENT_SERVER._websocket_sockets:  # if the socket is open.
            logger.debug("Activating Ping")

            self._status = False

            self._send_websocket_message(
                opcode=FrameOpcodes.ping
            )  # Send a ping frame to the client socket.

        return

    def _pong(self) -> None:
        self._send_websocket_message(
            opcode=FrameOpcodes.pong
        )  # Send a pong frame using _send_websocket_message method.

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
            logger.debug(f"Received Ping from Client")
            self._pong()  # Send a pong frame in response.
            return
        if (
            opcode == FrameOpcodes.pong
        ):  # Check if recieved frame opcode is a pong opcode.
            self._status = True

            logger.success(f"Received Pong from Client")
            return

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        if event in self._event_handlers:  # If the event is in _event_handlers.
            for handler in self._event_handlers[
                event
            ]:  # For each handler asinged to the event.
                handler(
                    *args,
                    **kwargs,  # Provide required positional arguments and key arguments.
                )  # Call the handler.

    def _trigger_event_from_message(self, final_message: dict | str) -> None:
        if type(final_message) == str:
            logger.warning(
                f"Message with no endpoint recieved: {final_message}"
            )  # Log the error, no execption is needed here.
            return

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

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0x80) >> 7 == 1

    def _handle_message(self) -> None:
        frame_in_bytes: bytes = b""  # Initialise frame_in_bytes.
        final_message: str = ""  # Initialise final_message.
        fragmented: bool = False  # Initialise fragmented.

        while True:
            frame_data = self.SOCKET.recv(self._BUFFER_SIZE)  # Read socket data.

            if frame_data == b"":
                # Connection closed, or no data received.
                break

            logger.debug("Handling websocket message")

            frame_in_bytes = frame_data  # set frame_in_bytes to frame_data.

            if not self._is_final_frame(frame_in_bytes):
                # This is a fragmented frame
                fragmented = True

                self._frame_decoder.decode_websocket_message(
                    frame_in_bytes=frame_in_bytes
                )  # Decode the given frame.

                message_payload = self._frame_decoder.payload_data.decode(
                    "utf-8"
                )  # Retrieve the decoded payload_data.

                final_message += (
                    message_payload  # Add the decoded message to the final message.
                )
                continue

            # This is a non-fragmented frame
            self._frame_decoder.decode_websocket_message(
                frame_in_bytes=frame_in_bytes
            )  # Decode the frame.

            control_opcode = (
                self._frame_decoder.opcode
            )  # Retrieve the opcode (control frames can't be fragmented).

            if check_if_control(opcode=control_opcode) and not fragmented:
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

            message_dict: dict = {}

            try:
                message_dict: dict = json.loads(
                    final_message
                )  # Load the final message (if a dictionary).
            except:
                pass

            self._trigger_event_from_message(
                final_message=message_dict if message_dict else final_message
            )  # Trigger the event given.

    def _listen_for_messages(self) -> None:
        critical = False  # Initialise critical.

        try:
            while self in self._PARENT_SERVER._http_sockets:
                readable_socket, writeable_socket, error_socket = select.select(
                    [self.SOCKET],
                    [self.SOCKET],
                    [self.SOCKET],
                    self._PARENT_SERVER._TIMEOUT,
                )

                if self.SOCKET.fileno() == -1:
                    # No data to be read, so carry on to the next cycle.
                    continue

                if self.SOCKET in error_socket:
                    critical = True
                    break

                if (
                    self in self._PARENT_SERVER._websocket_sockets
                    and self.SOCKET in readable_socket
                ):  # If the socket has opened a WebSocket connection.
                    self._handle_message()  # Handle the Websocket message.
                    continue

                if self.SOCKET in readable_socket:
                    self._PARENT_SERVER._handle_request(
                        socket=self
                    )  # Handle normal HTTP request.

        except Exception as e:  # If a Connection error occurs.
            print(e)
            critical = True  # Set cirital to True.

        if not critical:  # If no error has occured.
            logger.warning(f"Closed socket: {self.SOCKET}")

            return

        # If an error has occcured close the socket, to stop more errors occuring.
        self._close_socket(critical=critical)

        logger.critical(f"Socket Forcibly closed {self.SOCKET}")

        return

    def _heartbeat(self) -> None:
        while (
            self in self._PARENT_SERVER._websocket_sockets
        ):  # While the socket is open.
            self._ping()  # Ping the client.
            time.sleep(5)  # Every 5 seconds
