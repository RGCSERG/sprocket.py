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

from typing import Final, List

__all__: Final[List[str]] = ["FrameOpcodes"]


class FrameOpcodes:
    """
    Amount of bytes for each respective control frame in accordance with websocket protocol,
    (using specific control frame values defined in https://datatracker.ietf.org/doc/html/rfc6455)

    0x3-7 and 0xB-F are reserved (non-control/control frames respectively)
    """

    continuation: bytes = 0x0  # Denotes continuation frame.
    text: bytes = 0x1  # Denotes text frame.
    binary: bytes = 0x2  # Denotes binary frame.
    close: bytes = 0x8  # Denotes connection close frame.
    ping: bytes = 0x9  # Denotes ping frame.
    pong: bytes = 0xA  # Denotes pong frame.
