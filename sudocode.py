from abc import ABC, abstractmethod


class FrameEncoder(ABC):
    def __init__(self) -> None:
        """nothing to initialise yet"""

    @abstractmethod
    def encode_payload_to_frames(payload: str) -> WSFrame:
        """Takes in data as a string and converts it to a websocket frame"""
