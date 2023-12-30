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

import base64, hashlib, select, socket, threading, json  # Import used libaries.
from typing import (
    Any,
    Callable,
    Final,
    List,
    Dict,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for console logging.
from ..sockets import ServerSocket  # Import abstract class.
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..functions import (
    check_port,
    check_frame_size,
    check_if_control,
    check_endpoint,
)  # Import used functions.
from ..exceptions import (
    TCPPortException,
    FrameSizeException,
    WSEndpointException,
)  # Import used exceptions.
from .requesthandler import *  # Import RequestHandler.


__all__: Final[List[str]] = ["ServerSocketBaseImpl"]


class ServerSocketBaseImpl(ServerSocket):
    """
    Class for a WebSocket server implementation that handles WebSocket connections, messages and HTTP requests.
    """

    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        if PORT is not None and not check_port(
            PORT=PORT  # Checks if provided value is valid.
        ):  # Checks if TCP_PORT is not None, if not then checks whether the provided value is valid.
            raise TCPPortException  # If value provided is not valid, raise ValueError.

        # If no value provided or provided value valid, set _PORT to default value / provided value.
        self._PORT: int = PORT

        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not None, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.

        # Value not set in this class.

        if WS_ENDPOINT is not None and not check_endpoint(
            WS_ENDPOINT=WS_ENDPOINT  # Checks if provided value is valid.
        ):  # Checks if WS_ENDPOINT is not None, if not then checks whether the provided value is valid.
            raise WSEndpointException  # If value provided is not valid, raise ValueError.

        # If no value provided or provided value valid, set _WS_ENDPOINT to default value / provided value.
        self._WS_ENDPOINT: str = WS_ENDPOINT

        self._HOST: str = HOST  # Server Host domain.
        self._BUFFER_SIZE: int = BUFFER_SIZE  # Set buffer size (in bits).
        self._TIMEOUT: int = TIMEOUT  # Set select socket timeout.
        self._BACKLOG: int = BACKLOG  # Set sockets backlog.
        self._WEBSOCKET_GUID: str = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # Sets the GUID to the GUID defined in RFC6455
        self._LOCK = threading.Lock()  # Protect access to shared resources.
        # ---------------------- #
        self._rooms: Dict[str, list] = {}  # Initialise _rooms.
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.
        self._http_sockets: list = []  # Initialise _http_sockets.
        self._websocket_sockets: list = []  # Initialise websocket sockets.
        self._request_handler: HTTPRequestHandler = HTTPRequestHandler(
            WS_ENDPOINT=WS_ENDPOINT, HOST=HOST, PORT=PORT
        )  # Initialise _request_handler.
        self._frame_decoder: WebSocketFrameDecoder = WebSocketFrameDecoder(
            status=False
        )  # Initialise _frame_decoder.
        self._frame_encoder: WebSocketFrameEncoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=False
        )  # Initialise _frame_encoder.

        self._setup_socket()  # Setup socket.

    # Private methods.

    def _remove_socket_from_lists(self, socket: socket) -> None:
        if (
            socket in self._websocket_sockets
        ):  # If the given socket is in _websocket_sockets.
            self._websocket_sockets.remove(
                socket
            )  # Remove the given socket from _websocket_sockets.
        if socket in self._http_sockets:  # If the given socket is in _http_sockets.
            self._http_sockets.remove(socket)  # Remove it from _http_sockets.

        return

    def _send_websocket_message(
        self,
        socket: socket,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        logger.debug("Sending Message")

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload, opcode=opcode
        )  # Encoded the given payload and opcode to WebSocket frame(s).

        for frame in frames:  # For each frame created.
            socket.send(frame)  # Send the frame to the provided socket.

            return

    def _close_socket(self, socket: socket, critical: Optional[bool] = False) -> None:
        with self._LOCK:  # Protect access to shared resources.
            logger.warning("closing socket")

            if (
                socket in self._websocket_sockets and not critical
            ):  # If the socket is a WebSocket.
                self._send_websocket_message(
                    socket=socket, opcode=FrameOpcodes.close
                )  # Send a close frame.

            self._remove_socket_from_lists(
                socket=socket
            )  # Remove the socket from all active lists.

            self.leave_room(
                socket=socket
            )  # Remove given socket from all rooms (if in).

            self._trigger("disconnect", socket=socket)

            socket.close()  # Finnaly, close the socket.
            return

    def _setup_socket(self) -> None:
        self._server_socket: socket = socket.socket(  # Using the socket libary.
            socket.AF_INET,  # Using the AF_INET address family.
            socket.SOCK_STREAM,  # Using sock stream type SOCK_STREAM- socket for TCP communication.
        )  # Initialise the socket.
        self._server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  #  Enable re-use of the address and port.
        self._server_socket.bind(
            (self._HOST, self._PORT)
        )  # Bind the socket to specified host and port.

        self._http_sockets.append(
            self._server_socket
        )  # Append socket to _http_sockets.

        return

    def _create_sec_accept_key(self, sec_websocket_key: str) -> bytes:
        # Concatenate the provided key with the WebSocket GUID.

        concatenated_key: str = sec_websocket_key + self._WEBSOCKET_GUID

        # Generate SHA1 hash of the concatenated string.
        sha1_hash: bytes = hashlib.sha1(concatenated_key.encode()).digest()

        # Encode the hash in base64.
        encoded_key: bytes = base64.b64encode(sha1_hash)

        return encoded_key

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        if event in self._event_handlers:  # If the event is in _event_handlers.
            for handler in self._event_handlers[
                event
            ]:  # For each handler asinged to the event.
                handler(
                    *args,
                    **kwargs,  # Provide required positional arguments and key arguments.
                )  # Call the handler.

        return

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

    def _handle_handshake(self, socket: socket, headers: dict) -> None:
        sec_websocket_key = headers.get(
            "sec-websocket-key"
        )  # Retrieve the sec-websocket-key header.

        sec_accept = self._create_sec_accept_key(
            sec_websocket_key=sec_websocket_key
        ).decode()  # Create a Sec-Websocket-Accept value.

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {sec_accept}\r\n"
            "\r\n"
        ).encode(
            "utf-8"
        )  # Create valid response message.

        socket.send(response)  # Send the response back to the client.

        self._websocket_sockets.append(
            socket
        )  # Add the socket to the _websocket_sockets list.

        self._trigger(event="connection", socket=socket)  # Trigger connection event.

        return

    def _receive_http_request(self, socket: socket) -> str:
        request_data: bytes = b""  # Initialise request data.

        while True:
            http_chunk = socket.recv(self._BUFFER_SIZE)  # Read socket data.

            if not http_chunk:
                break  # Break the loop when no more data is received.

            request_data += http_chunk  # Add the chunk to the request data.

            if b"\r\n\r\n" in request_data:
                break  # Exit the loop when the entire request is received.

        decoded_request_data: str = request_data.decode(
            "utf-8"
        )  # Decode the full request.

        return decoded_request_data

    def _handle_request(self, socket: socket) -> None:
        logger.debug("Handling HTTP request")

        request_data: str = self._receive_http_request(
            socket=socket
        )  # Retrieve request_data.

        if not request_data:  # If no data recieved.
            self._close_socket(socket=socket)  # Close the socket (HTTP).
            return  # Stop the rest of the code executing.

        response, status = self._request_handler.process_request(
            request_data=request_data
        )  # Using instance of _request_handler get the response and status of the request.

        if not status:  # If not a WebSocket Handshake.
            socket.send(
                response.encode("utf-8")
            ) if response else None  # Send decoded response.
            self._close_socket(socket=socket)  # Close the socket (HTTP).
            return

        self._handle_handshake(
            socket=socket, headers=response
        )  # Handle the WebSocket handshake.

        return

    def _pong(self, socket: socket) -> None:
        self._send_websocket_message(
            socket=socket, opcode=FrameOpcodes.pong
        )  # Send pong frame.

        return

    def _check_control_frame(self, opcode: bytes, socket: socket) -> None:
        if opcode == FrameOpcodes.close:  # If the opcode is a close connection.
            self._close_socket(socket=socket)  # Close the socket.

            return

        if opcode == FrameOpcodes.ping:  # If the opcode is a ping frame.
            logger.debug(f"Recived Ping from {socket}")

            self._pong(socket=socket)  # Send a pong in response.

            self._trigger("ping")  # Trigger ping event.

            return

        if opcode == FrameOpcodes.pong:  # If the opcode is a pong frame.
            logger.debug(f"Recived Pong from {socket}")

            self._trigger("pong")  # Trigger pong event.

            return

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0x80) >> 7 == 1

    def _handle_message(self, socket: socket) -> None:
        frame_in_bytes: bytes = b""  # Initialise frame_in_bytes.
        final_message: str = ""  # Initialise final_message.
        fragmented: bool = False  # Initialise fragmented.

        while True:
            frame_data = socket.recv(self._BUFFER_SIZE)  # Read socket data.

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
                    opcode=control_opcode, socket=socket
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

    def _create_new_client_thread(self, client_socket: socket) -> None:
        critical = False  # Initialise critical.

        try:
            while client_socket in self._http_sockets:
                readable_socket, writeable_socket, error_socket = select.select(
                    [client_socket], [client_socket], [client_socket], self._TIMEOUT
                )

                if client_socket.fileno() == -1:
                    # No data to be read, so carry on to the next cycle.
                    continue

                if client_socket in error_socket:
                    critical = True
                    break

                if (
                    client_socket in self._websocket_sockets and readable_socket
                ):  # If the socket has opened a WebSocket connection.
                    self._handle_message(
                        socket=client_socket
                    )  # Handle the Websocket message.
                    continue

                if client_socket in readable_socket:
                    self._handle_request(
                        socket=client_socket
                    )  # Handle normal HTTP request.

        except:  # If a Connection error occurs.
            critical = True  # Set cirital to True.

        if not critical:  # If no error has occured.
            logger.warning(f"Closed socket: {client_socket}")

            return

        # If an error has occcured close the socket, to stop more errors occuring.
        self._close_socket(socket=client_socket, critical=critical)

        logger.critical(f"Socket Forcibly closed {client_socket}")

        return

    def _handle_connection(self) -> None:
        (
            new_socket,
            socket_address,
        ) = self._server_socket.accept()  # Accept the connection.

        self._http_sockets.append(
            new_socket
        )  # Append the socket to the active sockets list.

        logger.success(
            f"New Connection connection: {new_socket.fileno()} from address: {socket_address}"
        )

        client_listening_thread = threading.Thread(
            target=self._create_new_client_thread, args=[new_socket]
        )  # Create a new client listening thread.

        client_listening_thread.start()  # Start the client listening thread.

        return

    def _listen_for_messages(self) -> None:
        while self.main_thread:  # While the server is active.
            readable_server_socket: list = select.select(
                [self._server_socket], [], [], self._TIMEOUT
            )[
                0
            ]  # Check if server socket is readable..

            for socket in readable_server_socket:  # For each readable socket.
                if socket.fileno() == -1:
                    # There is no data to be read.
                    continue
                if socket == self._server_socket:  # If the socket is the server socket.
                    logger.success("Handling New HTTP connection")
                    self._handle_connection()  # Handle the incomming HTTP connection.
