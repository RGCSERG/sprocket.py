import json
import socket
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    List,
    NoReturn,
    Optional,
)

__all__: Final[List[str]] = ["TriggerTesting"]


class EventTrigger:
    def __init__(self) -> None:
        self._rooms: Dict[str, list] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}

    @property
    def handlers(self):
        return self._event_handlers

    def _trigger(self, event: str, *args: tuple, **kwargs: dict[str, Any]) -> None:
        # Trigger event handlers
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args, **kwargs)

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def to(self, room_name: str):
        if room_name not in self._rooms:
            self._rooms[room_name] = []

        return RoomEmitter(self, self._rooms[room_name])

    def _emit(
        self, event: str, payload: (str | bytes | dict | None), socket: socket
    ) -> None:
        json_data: dict = {event: payload}

        payload: str = json.dumps(json_data)

        frames = self._frame_encoder.encode_payload_to_frames(payload=payload)

        for frame in frames:
            self.send(frame)


class RoomEmitter:
    def __init__(self, trigger_testing: EventTrigger, room: list) -> None:
        self._trigger_testing = trigger_testing
        self._room: list = room

    def emit(self, event: str, payload: (str | bytes | dict | None)) -> None:
        for socket in self._room:
            self._trigger_testing.emit(event=event, payload=payload, socket=socket)


trigger = EventTrigger()


def main(socket):
    def print_x(x):
        print(x, socket)

    def print_y(y):
        print(y, socket)

    def print_z(z):
        print(z, socket)

    socket.on("x", print_x)
    socket.on("y", print_y)
    socket.on("z", print_z)


def recieve_message(message: str):
    print(message)


trigger.on("Send_Message", recieve_message)

trigger.on("Main", main)


trigger.to("1231231").emit("Send_Message", "message")
