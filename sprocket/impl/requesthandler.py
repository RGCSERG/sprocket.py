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

from http import HTTPStatus
from loguru import logger
from typing import (
    Any,
    Final,
    List,
    Literal,
)  # Used for type annotations and decloration.


__all__: Final[List[str]] = ["HTTPRequestHandler"]


class HTTPRequestHandler:
    def __init__(self, WS_ENDPOINT: str) -> None:
        self.WS_ENDPOINT = WS_ENDPOINT

        self.request_data: str = ""
        self.method: str = ""
        self.target: str = ""
        self.headers: dict = {}
        self.http_version: str = ""

    @staticmethod
    def _parse_request_line(request_line: list[str]) -> tuple[str, str, str]:
        method: str
        target: str
        http_version: str

        method, target, http_version = request_line.split(" ")
        return method, target, http_version

    def _parse_headers(self, headers: list[str]) -> dict:
        headers: dict = {
            header_name.lower(): header_value.strip()  # Headers should be set to lower case, for all mapping and classification rules.
            for line in headers
            if ":" in line
            for header_name, header_value in (line.split(":", 1),)
        }
        return headers

    def _validate_handshake(
        self, method: str, target: str, headers: dict, http_version: str
    ) -> bool:
        logger.debug("Handling WebSocket handshake request.")

        if method != "GET":
            return False

        if target != self.WS_ENDPOINT:
            return False

        try:
            _, version = http_version.split("/")
            http_version: float = float(version)
        except (ValueError, IndexError):
            return False  # Invalid HTTP version format.

        if http_version < 1.1:
            return False

        headers_valid: bool = (
            headers.get("upgrade", "") == "websocket"
            and headers.get("connection", "") == "Upgrade"
            and "sec-websocket-key" in headers
        )
        return headers_valid

    def _parse_request(self, request_data: str) -> tuple[str, str, dict, str] | None:
        # Split the request data into lines to parse individual components.
        request_list: list[str] = request_data.split("\r\n")

        if not request_list:
            return None

        # Parse the request line to extract method, target, and HTTP version
        method, target, http_version = self._parse_request_line(
            request_line=request_list[0]
        )

        # Parse headers
        headers: dict = self._parse_headers(headers=request_list[1:])

        return method, target, headers, http_version

    def process_request(
        self, request_data: str
    ) -> tuple[str, Literal[False]] | tuple[dict | Any, Literal[True]]:
        response_body = "<html><body><h1>Default bad response</h1></body></html>"
        response_headers = f"HTTP/1.1 {HTTPStatus.BAD_REQUEST}\r\nContent-Length: {len(response_body)}\r\n\r\n"

        full_response = response_headers + response_body

        self.request_data = request_data

        request = self._parse_request(request_data=self.request_data)

        method, target, headers, http_version = request

        self.method = method
        self.target = target
        self.headers = headers
        self.http_version = http_version

        if not request:
            return full_response, False

        if not self._validate_handshake(
            method=method, target=target, headers=headers, http_version=http_version
        ):
            logger.warning("Handshake invalid.")
            return full_response, False

        logger.success("Handshake valid.")

        return headers, True
