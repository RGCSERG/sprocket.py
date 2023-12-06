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

from loguru import logger
from typing import (
    Final,
    List,
    Literal,
)  # Used for type annotations and decloration.


__all__: Final[List[str]] = ["HTTPResponseHandler"]


class HTTPResponseHandler:
    def __init__(self, WEBSOCKET_KEY) -> None:
        self.WEBSOCKET_KEY = WEBSOCKET_KEY
        self.response_code: str = ""
        self.headers: dict = {}

    @staticmethod
    def _parse_response_code(http_code_line: str) -> Literal[0, 101]:
        response_code: Literal[101] = 101

        if "101" not in http_code_line:
            return 0

        return response_code

    def _validate_code_headers(self, response_code: int, headers: dict) -> bool:
        if response_code != 101:
            return False

        headers_valid: bool = (
            headers.get("upgrade", "") == "websocket"
            and headers.get("connection", "") == "Upgrade"
            and "sec-websocket-accept" in headers
        )

        return headers_valid

    def _parse_headers(self, headers: list[str]) -> dict:
        headers: dict = {
            header_name.lower(): header_value.strip()  # Headers should be set to lower case, for all mapping and classification rules.
            for line in headers
            if ":" in line
            for header_name, header_value in (line.split(":", 1),)
        }
        return headers

    def _parse_response(
        self, response_data: str
    ) -> tuple[Literal[0, 101], dict] | None:
        # Split the request data into lines to parse individual components.
        request_list: list[str] = response_data.split("\r\n")

        if not request_list:
            return None

        response_code: int = self._parse_response_code(request_list[0])

        headers: dict = self._parse_headers(headers=request_list[1:])

        return response_code, headers

    def validate_handshake_response(self, handshake_response: str) -> bool:
        response = self._parse_response(response_data=handshake_response)

        if not response:
            return False

        response_code, headers = response

        self.response_code = response_code
        self.headers = headers

        return self._validate_code_headers(response_code=response_code, headers=headers)
