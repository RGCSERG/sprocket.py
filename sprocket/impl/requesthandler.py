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
    """
    HTTPRequestHandler is responsible for handling any given incoming WebSocket handshake request over HTTP.

    Containing methods to parse the request data, validate the WebSocket handshake, and process the incoming requests,
    returning apropriate data.
    """

    def __init__(self, WS_ENDPOINT: str, HOST: str, PORT: int) -> None:
        """
        Args:
            WS_ENDPOINT str: The endpoint to which WebSocket hanshake Requests should be made.
        """
        self.WS_ENDPOINT: str = WS_ENDPOINT  # Set WS_ENDPOINT.
        self.HOST_DOMAIN: str = f"{HOST}:{PORT}"

        self.request_data: str = ""  # Initialise request_data.
        self.method: str = ""  # Initialise method.
        self.target: str = ""  # Initialise target.
        self.headers: dict = {}  # Initialise headers.
        self.http_version: str = ""  # Initialise http_version.

    @staticmethod
    def _parse_request_line(first_line: str) -> tuple[str, str, str]:
        """
        Parses the first line of the HTTP request, retrieving the request's method, target, and http version.

        Args:
            first_line str: the first line of the http request.

        Returns:
            tuple[str, str, str] denoting [method, target, http_version] respectively.
        """
        method: str  # set method type.
        target: str  # Set targert type.
        http_version: str  # Set http_version.

        method, target, http_version = first_line.split(
            " "
        )  # Provide values for each variable.
        return method, target, http_version

    def _parse_headers(self, headers: list[str]) -> dict:
        """
        Parses the headers of the request by iterating through the provided line list,
        then individually parses each line into a dictionary containing the headers' key-value pairs.

        Args:
            headers list[str]: All trailing lines after index 0.
        """

        # For each line in the headers list set the stored header and value to a key and value in the headers dictionary.
        headers: dict = {  # Headers should be set to lower case, for all mapping and classification rules.
            header_name.lower(): header_value.strip()  # Set Header values. Headers should be set to lower case, for all mapping and classification rules.
            for line in headers  # Iterate through the list.
            if ":" in line  # If a valid header line.
            for header_name, header_value in (
                line.split(":", 1),
            )  # Split the header line with a maximum of one split.
        }
        return headers

    def _validate_handshake(
        self, method: str, target: str, headers: dict, http_version: str
    ) -> bool:
        """
        Determines whether or not any given request is a valid (True) WebSocket handshake,
        for a given server.

        Args:
            method str: The method type of the given request.
            target str: The endpoint target of the given request.
            headers dict: The headers of the given requests in dictionary form.
            http_version str: The HTTP version of the request in str format.

        Returns:
            bool where True is a valid handshake and False is an invalid handshake.
        """
        logger.debug("Handling WebSocket handshake request.")

        if method != "GET":  # Checks whether the method is GET.
            return False  # If not return an invalid request (False).

        if (
            target != self.WS_ENDPOINT
        ):  # If the requests target is not the valid WS_ENDPOINT.
            return False  # Return an invalid request (False).

        try:
            _, version = http_version.split(
                "/"
            )  # Remove the '/' from the http_verions str.
            http_version: float = float(version)  # Convert the http_version to a float.
        except (
            ValueError,
            IndexError,
        ):  # If the value cannot be converted then it must be invalid.
            return False  # Invalid HTTP version format.

        if http_version < 1.1:  # Check if version is valid.
            return False  # If invalid return an invalid request (False).

        # Validate headers.
        headers_valid: bool = (  # Returned value should be bool.
            headers.get("upgrade", "")
            == "websocket"  # Check for upgrade header, and validate its value.
            and headers.get("connection", "")
            == "Upgrade"  # Check for connection header, and validate its value.
            and headers.get("host", "") == self.HOST_DOMAIN  # CORS validation.
            and "sec-websocket-key"
            in headers  # Check there is a valid sec-websocket-key value.
        )
        return headers_valid

    def _parse_request(self, request_data: str) -> tuple[str, str, dict, str] | None:
        """
        Parses the full request, and returns its individual components.

        Args:
            request_data str: The full request in str format.

        Returns:
            tuple[str, str, dict, str] denoting [method, target, headers, http_version] respectively,
            or None.
        """

        request_list: list[str] = request_data.split(
            "\r\n"  # Denotes an endline.
        )  # Split the request data into lines to parse individual components.

        if not request_list:  # If there is no data.
            return None  # Return early with None.

        method, target, http_version = self._parse_request_line(
            first_line=request_list[0]
        )  # Parse the request line to extract method, target, and HTTP version.

        headers: dict = self._parse_headers(headers=request_list[1:])  # Parse headers.

        return method, target, headers, http_version

    def process_request(
        self, request_data: str
    ) -> tuple[str, Literal[False]] | tuple[dict | Any, Literal[True]]:
        """
        Processes the full request, parsing each individual part of the request and then validating it.
        This method also provides the bad request response (if invalid) and the headers if the request is valid,
        so a handshake can be initiated.

        Args:
            request_data str: The full request in str format.

        Returns:
            tuple[str, Literal[False]] denoting [response, False representing a bad request],
            or tuple[dict | Any, Literal[True]] denoting [headers, True representing a valid request]
        """
        response_body = "<html><body><h1>This Server only accepts WebSocket connections.</h1></body></html>"  # Set invalid response.
        response_headers = f"HTTP/1.1 {HTTPStatus.BAD_REQUEST}\r\nContent-Length: {len(response_body)}\r\n\r\n"  # Set invalid response.

        full_response = (
            response_headers + response_body
        )  # Create full invalid response.

        self.request_data = request_data  # Set full request data to class attribute.

        request: tuple = self._parse_request(
            request_data=self.request_data
        )  # Parse the request.

        (
            method,
            target,
            headers,
            http_version,
        ) = request  # Retrieve each individual attribute.

        # Set each value to class attribute.
        self.method = method
        self.target = target
        self.headers = headers
        self.http_version = http_version

        if not request:  # Check if a request is present.
            return full_response, False  # If not return bad request response and False.

        if not self._validate_handshake(
            method=method, target=target, headers=headers, http_version=http_version
        ):  # Validate the handshake request.
            logger.warning("Handshake invalid.")
            return full_response, False  # If not return bad request response and False.

        logger.success("Handshake valid.")

        # If valid return headers and True.
        return headers, True
