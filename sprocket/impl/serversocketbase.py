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

import base64, hashlib, random, select, socket, threading, time, re  # Import used libaries.
from typing import (
    Any,
    Final,
    List,
    NoReturn,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for console logging.
from ..frame_models import (
    WebSocketFrameEncoder,
    WebSocketFrameDecoder,
    FrameOpcodes,
)  # Import used classes.
from ..sockets import ServerSocket  # Import Abstract model.
from ..functions import check_tcp_port, check_frame_size  # Import used functions.
from ..exceptions import TCPPortException, FrameSizeException  # Import used exceptions.

__all__: Final[List[str]] = ["ServerSocketBaseImpl"]

DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
content="text/html;charset=utf-8">\r\n
<TITLE>Default Response</TITLE></HEAD><BODY>\r\n
<H1>Default Response</H1>\r\n
<p>Default Response</p>\r\n
</BODY></HTML>\r\n\r\n"""


class ServerSocketBaseImpl(
    ServerSocket
):  # rework with new frame encoder and websocketframe class updates + comments
    def __init__(
        self,
        TCP_HOST: Optional[str] = "localhost",
        TCP_PORT: Optional[int] = 1000,
        TCP_BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
        DEFAULT_HTTP_RESPONSE: Optional[bytes] = DEFAULT_HTTP_RESPONSE,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        # Constructor Method
        if TCP_PORT is not None and not check_tcp_port(
            TCP_PORT=TCP_PORT  # Checks if provided value is valid.
        ):  # Checks if TCP_PORT is not none, if not then checks whether the provided value is valid.
            raise TCPPortException  # If value provided is not valid, raise ValueError
        else:
            # If no value provided, set _TCP_PORT to default value
            self._TCP_PORT = TCP_PORT

        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not none, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.
        else:
            # value not set in this class
            pass

        self._TCP_HOST: str = TCP_HOST  # Server Host domain.
        self._TCP_PORT: int = TCP_PORT  # Host domain port.
        self._TCP_BUFFER_SIZE: int = TCP_BUFFER_SIZE  # Set buffer size (in bits).
        self._WS_ENDPOINT: str = WS_ENDPOINT  # WebSocket connection route.
        self._TIMEOUT: int = TIMEOUT  # Set select socket timeout.
        self._DEFAULT_HTTP_RESPONSE: bytes = (
            DEFAULT_HTTP_RESPONSE  # Set default HTTP response.
        )
        self._BACKLOG: int = BACKLOG  # Set server backlog.
        self._WEBSOCKET_GUID: str = (
            self._generate_random_websocket_guid()
        )  # Generate a random WebSocket GUID for each instance.
        self._LOCK = threading.Lock()  # Protect access to shared resources.
        # ---------------------- #
        self._event_handlers: dict = {}  # Initialise _event_handlers.
        self._rooms: dict = {}  # Initialise _rooms.
        self._input_sockets: list = []  # Initialise _input sockets.
        self._ws_sockets: list = []  # Initialise websocket sockets.
        self._frame_decoder = WebSocketFrameDecoder(
            status=False
        )  # Initialise _frame_decoder.
        self._frame_encoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=False
        )  # Initialise _frame_encoder.

        self._setup_socket()  # Setup socket.

    # Private methods

    def _setup_socket(self) -> None:
        self._server_socket = socket.socket(  # Using the socket libary.
            socket.AF_INET,  # Using the AF_INET address family.
            socket.SOCK_STREAM,  # Using sock stream type SOCK_STREAM- socket for TCP communication.
        )  # Initialise the socket.
        self._server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  #  Enable reusing the address and port.
        self._server_socket.bind(
            (self._TCP_HOST, self._TCP_PORT)
        )  # Bind the socket to specified host and port.

        self._input_sockets.append(
            self._server_socket
        )  # Append socket to _input_sockets.

    @staticmethod
    def _generate_random_websocket_guid() -> str:
        # Characters that can be used in the GUID
        characters: str = "0123456789ABCDEF"

        # Generate a random 32-character string
        random_guid : str= "".join(random.choice(characters) for _ in range(32))

        # Format it as a WebSocket GUID
        formatted_guid : str= "-".join(
            [
                random_guid[:8],
                random_guid[8:12],
                random_guid[12:16],
                random_guid[16:20],
                random_guid[20:],
            ]
        )

        return formatted_guid

    def _listen_for_messages(self) -> NoReturn:
        while True:
            readable_sockets = select.select(
                self._input_sockets, [], [], self._TIMEOUT
            )[0]

            for sock in readable_sockets:
                if sock.fileno() == -1:
                    continue
                if sock == self._server_socket:
                    logger.debug("Handling main door socket")
                    self._handle_new_connection()

    def _handle_new_connection(self) -> None:
        client_socket, client_addr = self._server_socket.accept()
        logger.debug("New socket", client_socket.fileno(), "from address:", client_addr)
        self._input_sockets.append(client_socket)

        listen_thread = threading.Thread(
            target=self._create_new_client_thread, args=[client_socket]
        )
        listen_thread.start()

    def _create_new_client_thread(self, client_socket: socket) -> None:
        critical = False
        try:
            readable_sockets = select.select(
                self._input_sockets, self._ws_sockets, [], self._TIMEOUT
            )[0]
            while client_socket in readable_sockets:
                if client_socket.fileno() == -1:
                    continue
                elif client_socket in self._ws_sockets:
                    self._handle_websocket_message(client_socket)
                else:
                    logger.debug("Handling regular socket read")
                    self._handle_request(client_socket)
        except ConnectionResetError:
            critical = True
        if critical:
            if client_socket in self._ws_sockets:
                self._ws_sockets.remove(client_socket)
            self._input_sockets.remove(client_socket)
            self.leave_room(client_socket=client_socket)
            logger.critical(f"Socket Forcibly closed {client_socket}")
        else:
            logger.warning(f"Closed socket: {client_socket}")

    def _handle_request(self, client_socket) -> None:  # FIX THIS FUNCTION VERY BAD CODE
        logger.debug("Handling request from client socket:", client_socket.fileno())
        message = ""
        # Very naive approach: read until we find the last blank line
        while True:
            frame_in_bytes = self._read_recv(client_socket=client_socket)
            # Connnection on client side has closed.
            if len(frame_in_bytes) == 0:
                self._close_socket(client_socket)
                return
            message_segment = frame_in_bytes.decode()
            message += message_segment
            if len(message) > 4 and message_segment[-4:] == "\r\n\r\n":
                break

        logger.debug(f"Received message: {message}")

        (method, target, http_version, headers_map) = self._parse_request(message)

        logger.debug(
            f"method, target, http_version: {method}, {target}, {http_version}"
        )
        logger.debug(f"headers: {headers_map}")

        # We will know it's a websockets request if the handshake request is
        # present.
        if target == self._WS_ENDPOINT:
            logger.success("request to ws endpoint!")
            if self._is_valid_ws_handshake_request(
                method, target, http_version, headers_map
            ):
                self._handle_ws_handshake_request(client_socket, headers_map)
                return
            else:
                # Invalid WS request.
                client_socket.send(b"HTTP/1.1 400 Bad Request")
                self._close_socket(client_socket)
                return

        # For now, just return a 200. Should probably return length too, eh
        client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + DEFAULT_HTTP_RESPONSE)
        self._close_socket(client_socket)

    def _handle_ws_handshake_request(
        self, client_socket, headers_map
    ) -> None:  # HANDLE THIS FUNCTION AS WELL
        self._ws_sockets.append(client_socket)

        # To handle a WS handshake, we have to generate an accept key from the
        # sec-websocket-key and a magic string.
        sec_websocket_accept_value = self._generate_sec_websocket_accept(
            headers_map.get("sec-websocket-key")
        )

        # We can now build the response, telling the client we're switching
        # protocols while providing the key.
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {sec_websocket_accept_value.decode()}\r\n"
            "\r\n"
        )

        logged_response = response.strip("\r\n")

        logger.debug(f"response: {logged_response}")

        client_socket.send(response.encode("utf-8"))

        self._trigger("connection", client_socket)

    def _generate_sec_websocket_accept(self, sec_websocket_key) -> bytes:
        # We generate the accept key by concatenating the sec-websocket-key
        # and the GUID, Sha1 hashing it, and base64 encoding it.
        combined = sec_websocket_key + self._WEBSOCKET_GUID
        hashed_combined_string = hashlib.sha1(combined.encode())
        encoded = base64.b64encode(hashed_combined_string.digest())
        return encoded

    def _is_valid_ws_handshake_request(
        self, method, target, http_version, headers_map
    ) -> bool:  # FIX THIS CODE PRONTO
        # There are a few things to verify to see if it's a valid WS handshake.
        # First, the method must be get.
        is_get = method == "GET"
        # HTTP version must be >= 1.1. We can do a really naive check.
        http_version_number = float(http_version.split("/")[1])
        http_version_enough = http_version_number >= 1.1
        # Finally, we should have the right headers. This is a subset of what we'd
        # really want to check.
        headers_valid = (
            ("upgrade" in headers_map and headers_map.get("upgrade") == "websocket")
            and (
                "connection" in headers_map
                and headers_map.get("connection") == "Upgrade"
            )
            and ("sec-websocket-key" in headers_map)
        )
        return is_get and http_version_enough and headers_valid

    def _parse_request(self, request) -> tuple[Any, Any, Any, dict]:
        headers_map = {}
        # Assume headers and body are split by '\r\n\r\n' and we always have them.
        # Also assume all headers end with'\r\n'.
        # Also assume it starts with the method.
        split_request = request.split("\r\n\r\n")[0].split("\r\n")
        [method, target, http_version] = split_request[0].split(" ")
        headers = split_request[1:]
        for header_entry in headers:
            [header_name, value] = header_entry.split(": ")
            # Headers are case insensitive, so we can just keep track in lowercase.
            # Here's a trick though: the case of the values matter. Otherwise,
            # things don't hash and encode right!
            headers_map[header_name.lower()] = value
        return (method, target, http_version, headers_map)

    def _check_control_frame(self, opcode: bytes, client_socket: socket) -> None:
        if opcode == FrameOpcodes.close:
            self._close_socket(client_socket=client_socket)
            return
        if opcode == FrameOpcodes.ping:
            logger.debug(f"Recived Ping from {client_socket}")
            self._pong(client_socket=client_socket)
            return
        if opcode == FrameOpcodes.pong:
            logger.debug(f"Recived Pong from {client_socket}")
            return

    def _pong(self, client_socket: socket) -> None:
        self.send_websocket_message(
            client_socket=client_socket, opcode=FrameOpcodes.pong
        )

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        # Trigger event handlers
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args, **kwargs)

    def _handle_websocket_message(self, client_socket: socket) -> None:
        frame_in_bytes = b""
        final_message = ""

        while True:
            frame_data = self._read_recv(client_socket=client_socket)
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
                self._check_control_frame(
                    opcode=control_opcode, client_socket=client_socket
                )
                message_payload = self._frame_decoder.payload_data.decode("utf-8")
                final_message += message_payload
                break

        if final_message and frame_in_bytes:
            frame_in_bytes = b""
            self._trigger_message_event(final_message, client_socket)

    def _trigger_message_event(self, message: str, client_socket: socket) -> None:
        event_separator_index = message.find(":")
        if event_separator_index != -1:
            event_name = message[:event_separator_index]
            message = message[event_separator_index + 1 :]
            event_name = re.sub(r"^.*?(\w+)$", r"\1", event_name)
            message = re.sub(r"^.*?(\w+)$", r"\1", message)
            logger.debug(f"Received message: {message} , at endpoint {event_name}")
            self._trigger(event_name, message, client_socket)
        else:
            logger.debug(f"Received message: {message} , at  no endpoint")

    def _is_final_frame(self, frame_in_bytes: bytes) -> bool:
        # Check the FIN bit in the first byte of the frame.
        return (frame_in_bytes[0] & 0b10000000) >> 7 == 1

    def _read_recv(self, client_socket: socket) -> None:
        # Read data from the socket
        readable_sockets = select.select([client_socket], [], [], self._TIMEOUT)[0]

        if client_socket not in readable_sockets:
            return

        with self._LOCK:
            retry_count = 0
            max_retries = 5

            while retry_count < max_retries:
                data = client_socket.recv(self._TCP_BUFFER_SIZE)
                if data:
                    return data
                else:
                    retry_count += 1
                    delay = 2**retry_count
                    logger.warning(f"No data received, retrying in {delay} seconds...")
                    time.sleep(delay)

            logger.warning("Max retries reached. Unable to read data.")
            return None

    def _close_socket(self, client_socket: socket) -> None:
        with self._LOCK:
            logger.warning("closing socket")
            if client_socket in self._ws_sockets:
                self._ws_sockets.remove(client_socket)
            self._input_sockets.remove(client_socket)
            self.send_websocket_message(
                client_socket=client_socket, opcode=FrameOpcodes.close
            )
            self.leave_room(client_socket=client_socket)
            client_socket.close()
            return
