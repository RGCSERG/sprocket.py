import socket
from abc import ABC
from typing import Final, List, Optional


__all__: Final[List[str]] = ["SprocketSocketAbstract"]


class SprocketSocketAbstract(ABC):
    def __init__(
        self,
        SOCKET: socket,
        PARENT_SERVER,
        MAX_FRAME_SIZE: Optional[int] = 125,
        BUFFER_SIZE: Optional[int] = 8192,
    ) -> None:
        """
        Args:
            SOCKET socket: The Client socket to be used.
            PARENT_SERVER: The parent server implementation instance.
            BUFFER_SIZE int: Buffer size for reading data from sockets.
            MAX_FRAME_SIZE int: Maximum WebSocket frame size.

        _Args:
            _LOCK threading.Lock: Threading lock for synchronising access to shared resources.
            _event_handlers dict: Event handlers for WebSocket events.
            _rooms_joined set: The rooms that the client has joined.
            _status bool: Determines whether or not the socket is open.
            _frame_decoder WebsocketFrame: Class for decoding WebSocket frames.
            _frame_encoder WebSocketFrameEncoder: Class for encoding any given payload into WebSocket frame(s).
        """
