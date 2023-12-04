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


import random, select, socket, threading, time, json, base64  # Import used libaries.
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

        self._setup_socket()  # Setup socket.

    @staticmethod
    def _generate_random_websocket_key() -> str:
        # Generate a random WebSocket key
        characters = "0123456789ABCDEF"  # Characters to be used.

        random_key = "".join(
            random.choice(characters) for _ in range(16)
        )  # Generate a random 16 byte string.

        encoded_random_key = base64.b64encode(
            random_key
        )  # Base 64 encoded the random string.

        return encoded_random_key

    def _setup_socket(self) -> None:
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.setblocking(True)

    def _listen_for_messages(self) -> None:
        while self._socket_open:
            self._handle_message()

    def _perform_websocket_handshake(self) -> bool:
        # Perform WebSocket handshake
        logger.debug("Performing WebSocket Handshake")

        request = (
            f"GET /websocket HTTP/1.1\r\n"
            f"Host: {self._HOST}:{self._PORT}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self._WEBSOCKET_KEY}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("utf-8")

        self._client_socket.send(request)

        response = self._read_recv().decode("utf-8")
        if "101 Switching Protocols" in response:
            self._trigger(event="connection", socket=self._client_socket)
            return True
        else:
            return False

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        if event in self._event_handlers:  # If the event is in _event_handlers.
            for handler in self._event_handlers[
                event
            ]:  # For each handler asinged to the event.
                handler(
                    *args,
                    **kwargs,  # Provide required positional arguments and key arguments.
                )  # Call the handler.
