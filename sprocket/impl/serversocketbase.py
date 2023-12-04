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

import base64, hashlib, random, select, socket, threading, time, json  # Import used libaries.
from typing import (
    Any,
    Callable,
    Final,
    List,
    Literal,
    Dict,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for console logging.
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..functions import check_port, check_frame_size  # Import used functions.
from ..exceptions import TCPPortException, FrameSizeException  # Import used exceptions.
from .requesthandler import *


__all__: Final[List[str]] = ["ServerSocketBaseImpl"]


class ServerSocketBaseImpl:
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

        self._HOST: str = HOST  # Server Host domain.
        self._PORT: int = PORT  # Host domain port.
        self._BUFFER_SIZE: int = BUFFER_SIZE  # Set buffer size (in bits).
        self._WS_ENDPOINT: str = WS_ENDPOINT  # WebSocket connection route.
        self._TIMEOUT: int = TIMEOUT  # Set select socket timeout.
        self._BACKLOG: int = BACKLOG  # Set server backlog.
        self._WEBSOCKET_GUID: str = (
            self._generate_random_websocket_guid()
        )  # Generate a random WebSocket GUID for each instance.
        self._LOCK = threading.Lock()  # Protect access to shared resources.
        # ---------------------- #
        self._rooms: Dict[str, list] = {}  # Initialise _rooms.
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.
        self._active_sockets: list = []  # Initialise _active_sockets.
        self._websocket_sockets: list = []  # Initialise websocket sockets.
        self._request_handler: HTTPRequestHandler = HTTPRequestHandler(
            WS_ENDPOINT=WS_ENDPOINT
        )
        self._frame_decoder: WebSocketFrameDecoder = WebSocketFrameDecoder(
            status=False
        )  # Initialise _frame_decoder.
        self._frame_encoder: WebSocketFrameEncoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=False
        )  # Initialise _frame_encoder.

        self._setup_socket()  # Setup socket.

    @staticmethod
    def _generate_random_websocket_guid() -> str:
        # Characters that can be used in the GUID
        characters: str = "0123456789ABCDEF"

        # Generate a random 32-character string
        random_guid: str = "".join(random.choice(characters) for _ in range(32))

        # Format it as a WebSocket GUID
        formatted_guid: str = "-".join(
            [
                random_guid[:8],
                random_guid[8:12],
                random_guid[12:16],
                random_guid[16:20],
                random_guid[20:],
            ]
        )

        return formatted_guid

    def _remove_socket_from_lists(self, socket: socket) -> None:
        if socket in self._websocket_sockets:
            self._websocket_sockets.remove(socket)
        if socket in self._active_sockets:
            self._active_sockets.remove(socket)

    def _send_websocket_message(
        self,
        socket: socket,
        payload: Optional[str] = "",
        opcode: Optional[bytes] = 0x1,
    ) -> None:
        """
        Send a WebSocket message to a specific client.
        This method sends a WebSocket message to a specific client identified by the provided socket.

        Args:
            socket socket: The client socket to send the message to.
            message Optional[str]: The message to send to the client.
            event Optional[str]: An optional event identifier for the message.
            opcode Optional[bytes]: The WebSocket frame opcode.
        """
        logger.debug("Sending Message")

        frames = self._frame_encoder.encode_payload_to_frames(
            payload=payload, opcode=opcode
        )

        for frame in frames:
            socket.send(frame)

    def _close_socket(self, socket: socket) -> None:
        with self._LOCK:
            logger.warning("closing socket")

            self._remove_socket_from_lists(socket=socket)

            self._send_websocket_message(socket=socket, opcode=FrameOpcodes.close)
            self.leave_room(socket=socket)

            socket.close()
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

        self._active_sockets.append(
            self._server_socket
        )  # Append socket to _active_sockets.

    def _create_sec_accept_key(self, sec_websocket_key: str) -> bytes:
        # Concatenate the provided key with the WebSocket GUID
        concatenated_key: str = sec_websocket_key + self._WEBSOCKET_GUID

        # Generate SHA1 hash of the concatenated string
        sha1_hash: bytes = hashlib.sha1(concatenated_key.encode()).digest()

        # Encode the hash in base64
        encoded_key: bytes = base64.b64encode(sha1_hash)

        return encoded_key

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

    def _emit(
        self, event: str, socket: socket, payload: (str | bytes | dict | None) = ""
    ) -> None:
        json_data: dict = {event: payload}

        payload: str = json.dumps(json_data)

        frames = self._frame_encoder.encode_payload_to_frames(payload=payload)

        for frame in frames:
            socket.send(frame)

    def _handle_handshake(self, socket: socket, headers: dict) -> None:
        self._websocket_sockets.append(socket)

        sec_websocket_key = headers.get("sec-websocket-key")

        sec_accept = self._create_sec_accept_key(
            sec_websocket_key=sec_websocket_key
        ).decode()

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {sec_accept}\r\n"
            "\r\n"
        ).encode("utf-8")

        socket.send(response)

        self._trigger(event="connection", socket=socket)

    def _read_recv(self, socket: socket) -> Any | None:
        # Read data from the socket
        readable_sockets: list = select.select([socket], [], [], self._TIMEOUT)[0]

        if socket not in readable_sockets:
            return None

        with self._LOCK:
            retry_count: int = 0
            MAX_RETRIES: Literal[5] = 5

            while retry_count < MAX_RETRIES and socket in readable_sockets:
                data = socket.recv(self._BUFFER_SIZE)
                if data:
                    return data
                else:
                    retry_count += 1
                    delay: int = (0.1 * retry_count) ** 2
                    logger.warning(f"No data received, retrying in {delay} seconds...")
                    time.sleep(delay)

            logger.critical("Max retries reached. Unable to read data.")
            return None

    def _receive_http_request(self, socket: socket) -> str:
        request_data: bytes = b""  # Initialise request data.

        while True:
            http_chunk = self._read_recv(socket=socket)

            if not http_chunk:
                break  # Break the loop when no more data is received.

            request_data += http_chunk

            if b"\r\n\r\n" in request_data:
                break  # Exit the loop when the entire request is received.

        decoded_request_data: str = request_data.decode("utf-8")
        return decoded_request_data

    def _handle_request(self, socket: socket) -> None:
        logger.debug("Handling HTTP request")
        request_data: str = self._receive_http_request(socket=socket)

        if not request_data:
            self._close_socket(socket=socket)
            return

        response, status = self._request_handler.process_request(
            request_data=request_data
        )

        if not status:
            socket.send(response.encode("utf-8")) if response else None
            self._close_socket(socket=socket)
            return

        self._handle_handshake(socket=socket, headers=response)
        return

    def _pong(self, socket: socket) -> None:
        self._send_websocket_message(socket=socket, opcode=FrameOpcodes.pong)

    def _check_control_frame(self, opcode: bytes, socket: socket) -> None:
        if opcode == FrameOpcodes.close:
            self._close_socket(socket=socket)
            return
        if opcode == FrameOpcodes.ping:
            logger.debug(f"Recived Ping from {socket}")
            self._pong(socket=socket)
            return
        if opcode == FrameOpcodes.pong:
            logger.debug(f"Recived Pong from {socket}")
            return

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0x80) >> 7 == 1

    def _handle_message(self, socket: socket) -> None:
        frame_in_bytes: bytes = b""
        final_message: str = ""

        while True:
            frame_data = self._read_recv(socket=socket)
            if frame_data == None:
                # Connection closed, or no data received.
                break

            logger.debug("Handling websocket message")

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
                self._check_control_frame(opcode=control_opcode, socket=socket)
                message_payload = self._frame_decoder.payload_data.decode("utf-8")
                final_message += message_payload
                break

        if final_message and frame_in_bytes:
            frame_in_bytes = b""
            message_dict: dict = json.loads(final_message)

            self._trigger_event_from_message(final_message=message_dict)

    def _create_new_client_thread(self, client_socket: socket) -> None:
        try:
            readable_sockets: list = select.select(
                self._active_sockets, self._websocket_sockets, [], self._TIMEOUT
            )[0]

            while client_socket in readable_sockets:
                if client_socket.fileno() == -1:
                    # self._remove_socket_from_lists(socket=client_socket)
                    continue
                elif client_socket in self._websocket_sockets:
                    self._handle_message(socket=client_socket)
                else:
                    self._handle_request(socket=client_socket)

        except ConnectionResetError:
            critical = True

        if not critical:
            logger.warning(f"Closed socket: {client_socket}")
            return

        self._remove_socket_from_lists(socket=client_socket)
        self.leave_room(socket=client_socket)

        logger.critical(f"Socket Forcibly closed {client_socket}")

        return

    def _handle_connection(self) -> None:
        new_socket, socket_address = self._server_socket.accept()
        self._active_sockets.append(new_socket)

        logger.success(
            "New WebSocket connection: ",
            new_socket.fileno(),
            " from address: ",
            socket_address,
        )

        client_listening_thread = threading.Thread(
            target=self._create_new_client_thread, args=[new_socket]
        )
        client_listening_thread.start()

        return

    def _listen_for_messages(self) -> None:
        while True:
            if not self.main_thread:
                break
            readable_sockets: list = select.select(
                self._active_sockets, [], [], self._TIMEOUT
            )[0]

            for socket in readable_sockets:
                if socket.fileno() == -1:
                    self._remove_socket_from_lists(socket=socket)
                if socket == self._server_socket:
                    logger.success("Handling incoming HTTP message.")
                    self._handle_connection()
