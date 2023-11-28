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
from typing import Final, List, Union  # Used for type annotations and decloration.


__all__: Final[List[str]] = ["HTTPRequestHandler"]


class HTTPRequestHandler:
    def __init__(self) -> None:
        self.request_data: str = ""
        self.method: str = ""
        self.target: str = ""
        self.headers: dict = {}
        self.http_version: str = ""

    def process_request(self, request_data: str) -> Union[str, None]:
        # Parse the HTTP request

        self.request_data = request_data

        request = self._parse_request(self.request_data)

        if not request:
            response_body = "<html><body><h1>Default bad response</h1></body></html>"
            response_headers = f"HTTP/1.1 {HTTPStatus.BAD_REQUEST}\r\nContent-Length: {len(response_body)}\r\n\r\n"
            return response_headers + response_body

        method, target, headers, http_version = request

        self.method = method
        self.target = target
        self.headers = headers
        self.http_version = http_version

        response_body = "<html><body><h1>Default response</h1></body></html>"
        response_headers = (
            f"HTTP/1.1 {HTTPStatus.OK}\r\nContent-Length: {len(response_body)}\r\n\r\n"
        )
        return response_headers + response_body

    def _parse_request(self, request_data: str) -> tuple[str, str, dict, str]:
        # Split the request data into lines to parse individual components
        request_lines: list[str] = request_data.split("\r\n")

        if not request_lines:
            return None

        # Parse the request line to extract method, target, and HTTP version
        method, target, http_version = self._parse_request_line(request_lines[0])

        # Parse headers
        headers: dict = self._parse_headers(request_lines[1:])

        return method, target, headers, http_version

    def _parse_request_line(self, request_line: list[str]) -> tuple[str, str, str]:
        method: str
        target: str
        http_version: str

        method, target, http_version = request_line.split(" ")
        return method, target, http_version

    def _parse_headers(self, header_lines: list[str]) -> dict:
        headers: dict = {}
        for line in header_lines:
            if ":" in line:
                header_name, header_value = line.split(":", 1)
                header_name = header_name.strip()
                header_value = header_value.strip()
                headers[header_name.lower()] = header_value
        return headers
