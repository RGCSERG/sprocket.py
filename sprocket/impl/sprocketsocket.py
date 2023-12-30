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


import base64, hashlib, select, socket, threading, json, time  # Import used libaries.
from typing import (
    Any,
    Callable,
    Final,
    List,
    Dict,
    Optional,
)  # Used for type annotations and decloration.
from loguru import logger  # Used for console logging.
from .serversocket import ServerSocket  # Import abstract class.
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

__all__: Final[List[str]] = ["SprocketSocket"]


class SprocketSocket:
    def __init__(
        self,
        SOCKET: socket,
        PARENT_SERVER: ServerSocket,
        MAX_FRAME_SIZE: Optional[int] = 125,
        BACKLOG: Optional[int] = 5,
    ) -> None:
        if MAX_FRAME_SIZE is not None and not check_frame_size(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE  # Checks whether provided value is valid.
        ):  # Checks if MAX_FRAME_SIZE is not None, if not then checks whether the provided value is valid.
            raise FrameSizeException  # If value provided is not valid raise ValueError.

        self._SOCKET: socket = SOCKET
        self._PARENT_SERVER: ServerSocket = PARENT_SERVER
        self._BACKLOG: int = BACKLOG  # Set sockets backlog.
        self._LOCK = threading.Lock()  # Protect access to shared resources.
        # ---------------------- #
        self._event_handlers: Dict[
            str, List[Callable]
        ] = {}  # Initialise _event_handlers.
        self._socket_open = False  # Initialise _socket_open to open (True).
        self._frame_decoder: WebSocketFrameDecoder = WebSocketFrameDecoder(
            status=False
        )  # Initialise _frame_decoder.
        self._frame_encoder: WebSocketFrameEncoder = WebSocketFrameEncoder(
            MAX_FRAME_SIZE=MAX_FRAME_SIZE, IS_MASKED=False
        )  # Initialise _frame_encoder.
