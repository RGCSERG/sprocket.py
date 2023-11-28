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
from .requesthandler import *


__all__: Final[List[str]] = ["ServerSocketBaseImpl"]

DEFAULT_HTTP_RESPONSE = b"""<HTML><HEAD><meta http-equiv="content-type"
content="text/html;charset=utf-8">\r\n
<TITLE>Default Response</TITLE></HEAD><BODY>\r\n
<H1>Default Response</H1>\r\n
<p>Default Response</p>\r\n
</BODY></HTML>\r\n\r\n"""


class ServerSocketBaseImpl:
    def __init__(
        self,
        HOST: Optional[str] = "localhost",
        PORT: Optional[int] = 1000,
        BUFFER_SIZE: Optional[int] = 8192,
        WS_ENDPOINT: Optional[str] = "/websocket",
        MAX_FRAME_SIZE: Optional[int] = 125,
        TIMEOUT: Optional[int] = 5,
        DEFAULT_HTTP_RESPONSE: Optional[bytes] = DEFAULT_HTTP_RESPONSE,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        if PORT is not None and not check_tcp_port(
            PORT=PORT  # Checks if provided value is valid.
        ):  # Checks if TCP_PORT is not none, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid, raise ValueError
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
        self._active_sockets: list = []  # Initialise _active_sockets.
        self._ws_sockets: list = []  # Initialise websocket sockets.
        self._request_handler: HTTPRequestHandler = HTTPRequestHandler()
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
        if socket in self._ws_sockets:
            self._ws_sockets.remove(socket)
        if socket in self._active_sockets:
            self._active_sockets.remove(socket)

    
    def _close_socket(self, socket: socket) -> None:
        with self._LOCK:
            logger.warning("closing socket")
            
            self._remove_socket_from_lists(socket=socket)

            self.send_websocket_message(
                client_socket=socket, opcode=FrameOpcodes.close
            )
            self.leave_room(client_socket=socket)

            socket.close()
            return

    def _setup_socket(self) -> None:
        self._server_socket : socket= socket.socket(  # Using the socket libary.
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
    


    def _receive_http_request(self, socket:socket) ->  str:
        request_data:bytes = b"" # Initialise request data.

        while True:
            http_chunk = socket.recv(self._BUFFER_SIZE)

            if not http_chunk:
                break # Break the loop when no more data is received.

            request_data += http_chunk

            if b"\r\n\r\n" in request_data:
                break  # Exit the loop when the entire request is received.
        
        decoded_request_data: str = request_data.decode("utf-8")
        return decoded_request_data
    
    def _handle_request(self, socket: socket) -> None:
        logger.debug("Handling HTTP request from: ", socket.fileno())
        request_data : str= self._receive_http_request(socket=socket)

        if not request_data:
            self._close_socket(socket=socket)
            return

        response = self._request_handler.process_request(request_data=request_data)
        
        if response:
            socket.send(response.encode("utf-8"))
            self._close_socket(socket=socket)
        
        self._close_socket(socket=socket)



    def _handle_websocket_message(self, socket: socket) -> None:
        frame_in_bytes = b""
        final_message = ""

        while True:
            frame_data = self._read_recv(client_socket=socket)
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
                    opcode=control_opcode, client_socket=socket
                )
                message_payload = self._frame_decoder.payload_data.decode("utf-8")
                final_message += message_payload
                break

        if final_message and frame_in_bytes:
            frame_in_bytes = b""
            self._trigger_message_event(final_message, client_socket)

    def _create_new_client_thread(self, client_socket: socket) -> None:
        try:
            readable_sockets = select.select(
                self._active_sockets, self._ws_sockets, [], self._TIMEOUT)[0]
            
            while client_socket in readable_sockets:
                if client_socket.fileno() == -1:
                    self._remove_socket_from_lists(socket=client_socket)
                if client_socket in self._ws_sockets:
                    self._handle_websocket_message(socket=client_socket)
                
                self._handle_request(socket==client_socket)
    

    def _handle_new_connection(self) -> None:
        client_socket, client_address = self._server_socket.accept()
        logger.success(
            "Handled new connection",
            client_socket.fileno(),
            " from address: ",
            client_address,
        )
        self._active_sockets.append(client_socket)

        client_listening_thread = threading.Thread(target=self._create_new_client_thread, args=[client_socket])
        client_listening_thread.start()


    def _listen_for_messages(self) -> None:
        while True:
            readable_sockets = select.select(
                self._active_sockets, [], [], self._TIMEOUT
            )[0]

            for socket in readable_sockets:
                if socket.fileno() == -1:
                    self._remove_socket_from_lists(socket=socket)
                if socket == self._server_socket:
                    logger.success("Handling incoming HTTP message.")
                    self._handle_new_connection()
