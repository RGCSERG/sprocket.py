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

from typing import (
    Final,
    List,
    Literal,
)  # Used for type annotations and decloration.


__all__: Final[List[str]] = ["HTTPResponseHandler"]


class HTTPResponseHandler:
    """
    HTTPResponseHandler is responsible for handling any given incoming WebSocket handshake response from a server, over HTTP.

    Containing methods to parse and validate the response data.
    """

    def __init__(self) -> None:
        """
        Initialiser method.
        """

        self.response_code: str = ""  # Initialise response code.
        self.headers: dict = {}  # Initialise headers dictionary.

    @staticmethod
    def _parse_response_code(http_code_line: str) -> Literal[0, 101]:
        """
        Parses the response code from the first line of the response.

        Args:
            http_code_line str: The first line of the response data.

        Returns:
            response_code Literal[0, 101]: The response code of the response,
            where 0 denotes an invalid response and 101 the correct response code.
        """

        response_code: Literal[
            101
        ] = 101  # Set the response code to the accepted value.

        if "101" not in http_code_line:  # If the response code is not 101.
            return 0  # Return a failed response.

        return response_code  # Return 101 as the response code.

    def _parse_headers(self, headers: list[str]) -> dict:
        """
        Parses the headers from the remaining lines of the response.

        Args:
            headers list[str]: The remaining lines of the response (which contain headers).

        Returns:
            headers dict: The headers from the response converted to a key: value dictionary.
        """

        headers: dict = {
            header_key.lower(): header_value.strip()  # Headers should be set to lower case, for all mapping and classification rules.
            for line in headers  # For each line in the headers list.
            if ":" in line  # If a valid header line is detected.
            for header_key, header_value in (
                line.split(":", 1),
            )  # Split the line into the key and the value.
        }

        return headers

    def _parse_response(
        self, response_data: str
    ) -> tuple[Literal[0, 101], dict] | None:
        """
        Parses the full response, and returns the HTTP code and headers in a tuple.

        Args:
            response_data  str: The full response in str format.

        Returns:
            tuple[Literal[0, 101], dict] denoting [response_code, headers] or None.
        """

        request_list: list[str] = response_data.split(
            "\r\n"
        )  # Split the request data into lines to parse individual components.

        if not request_list:  # If the response is not in a valid format.
            return None  # Return no data.

        response_code: int = self._parse_response_code(
            request_list[0]
        )  # Parse the response code, from the first line of the response.

        headers: dict = self._parse_headers(
            headers=request_list[1:]
        )  # Parse the headers from the remaining lines.

        return response_code, headers

    def _validate_code_headers(self, response_code: int, headers: dict) -> bool:
        """
        Validates the response code, and the response headers.

        Args:
            response_code int: The HTTP code of the response.
            headers dict: A key: value dictionary of the response headers.

        Returns:
            bool for a valid or invalid response, represented by True or False.
        """

        if response_code != 101:  # If the response code is not 101.
            return False  # Return an invalid response.

        headers_valid: bool = (
            headers.get("upgrade", "")
            == "websocket"  # Check that an upgrade header is present and that its value is valid.
            and headers.get("connection", "")
            == "Upgrade"  # Check that an connection header is present and that its value is valid.
            and "sec-websocket-accept"
            in headers  # Check that the sec-websocket-accept header is present.
        )  # Return as a bool.

        return headers_valid

    def validate_handshake_response(self, handshake_response: str) -> bool:
        """
        Validates any given WebSocket handhsake response from a server,
        by parsing the response and checking validating each component seperately.

        Args:
            hanshake_response str: The handshake response in str format.

        Returns:
            bool for a valid or invalid response, represented by True or False.
        """

        response = self._parse_response(
            response_data=handshake_response
        )  # Parse the response.

        if not response:  # If no response.
            return False  # Return an invalid response.

        (
            response_code,
            headers,
        ) = response  # Set the response code and headers from the response tuple.

        # Set to class attributes.
        self.response_code = response_code
        self.headers = headers

        return self._validate_code_headers(response_code=response_code, headers=headers)
