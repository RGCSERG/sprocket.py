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
    Optional,
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

        self._cors_middleware_enabled: bool = (
            False  # Initialise cors_middleware_enabled bool.
        )
        self._cors_allow_origins: List[str] = [
            f"http://{HOST}:{PORT}"
        ]  # Initialise allowed origins
        self._cors_allow_credentials: bool = True  # Initialise _cors_allow_credentials.
        self._cors_allow_methods: List[str] = ["*"]  # Initialise _cors_allow_methods.
        self._cors_allow_headers: List[str] = ["*"]  # Initialise _cors_allow_headers.

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

        Returns:
            headers dict: The parsed headers.
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

    def _check_if_ws_request(self, method: str, target: str) -> bool:
        """
        Determines if any given HTTP request is a WebSocket handshake request.

        Args:
            method str: The method type of the given request.
            target str: The endpoint target of the given request.

        Returns:
            bool where True is a handshake and False is not a handshake.
        """
        if method != "GET":  # Checks whether the method is GET.
            return False  # If not return an invalid request (False).

        if (
            target != self.WS_ENDPOINT
        ):  # If the requests target is not the valid WS_ENDPOINT.
            return False  # Return an invalid request (False).

        return True

    def _validate_headers(self, headers: dict) -> bool:
        """
        Validates the headers.

        Args:
            headers (dict): The headers of the given requests in dictionary form.

        Returns:
            headers_valid bool: True if headers are valid; False otherwise.
        """

        headers_valid: bool = (  # Returned value should be bool.
            headers.get("upgrade", "")
            == "websocket"  # Check for upgrade header, and validate its value.
            and headers.get("connection", "")
            == "Upgrade"  # Check for connection header, and validate its value.
            and headers.get("host", "")
            == self.HOST_DOMAIN  # Host is the same as server address.
            and "sec-websocket-key"
            in headers  # Check there is a valid sec-websocket-key value.
        )

        return headers_valid

    def _validate_handshake(self, headers: dict, http_version: str) -> bool:
        """
        Determines whether or not any given request is a valid (True) WebSocket handshake,
        for a given server.

        Args:
            headers dict: The headers of the given requests in dictionary form.
            http_version str: The HTTP version of the request in str format.

        Returns:
            bool where True is a valid handshake and False is an invalid handshake.
        """

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

        headers_valid: bool = self._validate_headers(
            headers=headers
        )  # Validate headers.
        return headers_valid

    def _cors_validation(
        self, method: str, headers: dict
    ) -> tuple[str, Literal[False]] | tuple[dict, Literal[True]]:
        """
        Validates the CORS policy if active, otherwise validates the origin of the request.

        Args:
            method str: The method type of the given request.
            headers dict: The headers of the given requests in dictionary form.

        Returns:
            tuple[str, Literal[False]] denoting [CORS violation response, False for violation]
            or tuple[dict, Literal[True]] denoting [headers, True for valid].
        """

        response_body = "<html><body><h1>Origin, Method, or specific header not allowed</h1></body></html>"  # Set CORS violation response.
        response_headers = f"HTTP/1.1 {HTTPStatus.FORBIDDEN}\r\nContent-Length: {len(response_body)}\r\n\r\n"  # Set CORS violation response.

        origin = headers.get("origin", "")  # Retrieve origin.

        full_response = (
            response_headers + response_body
        )  # Create full CORS violation response.

        if not self._cors_middleware_enabled:
            # If CORS not enabled.

            if "127.0.0.1" not in origin:  # Check origin against host domain.
                # Handle CORS violation.
                return full_response, False

            # Return valid response.
            return (
                headers,
                True,
            )  # Headers aren't needed in the return but its useful to fill the tuple.

        # If CORS enabled.

        if self._cors_allow_credentials:  # Handle CORS credentials if allowed.
            # Basic CORS credentials response.

            response_headers += f"Access-Control-Allow-Origin: {', '.join(self._cors_allow_origins)}\r\n"  # Set Access-Control-Allow-Origin header.
            response_headers += f"Access-Control-Allow-Methods: {', '.join(self._cors_allow_methods)}\r\n"  # Set Access-Control-Allow-Methods header.
            response_headers += f"Access-Control-Allow-Headers: {', '.join(self._cors_allow_headers)}\r\n"  # Set Access-Control-Allow-Headers header.

            full_response = (
                response_headers + response_body
            )  # Create full CORS violation response.

        if (
            origin
            not in self._cors_allow_origins  # Check origin against allowed origins.
            and "*" not in self._cors_allow_origins  # Check that * wildcard not played.
        ):
            # Handle CORS violation.
            return full_response, False

        if (
            method
            not in self._cors_allow_methods  # Check method against allowed methods.
            and "*" not in self._cors_allow_methods  # Check that * wildcard not played.
        ):
            # Handle CORS violation.
            return full_response, False

        if "*" in self._cors_allow_headers:  # If * wildcard played.
            # Save proccessing power and allow all.
            pass

        else:
            headers_valid: bool = set(headers.keys()).issubset(
                self._cors_allow_headers
            )  # Check all headers are within CORS policy.

            if not headers_valid:  # If invalid.
                # Handle CORS violation.
                return full_response, False

        # Return valid response.
        return headers, True

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

    def enable_cors_middleware(
        self,
        allow_origins: Optional[List[str]],
        allow_credentials: Optional[bool],
        allow_methods: Optional[List[str]],
        allow_headers: Optional[List[str]],
    ) -> None:
        """
        Enables CORS middleware with specified settings.

        Args:
            allow_origins list: List of allowed origins.
            allow_credentials bool: Allow credentials flag.
            allow_methods list: List of allowed methods.
            allow_headers list: List of allowed headers.
        """
        self._cors_allow_origins = (
            allow_origins if allow_origins != None else self._cors_allow_origins
        )  # Set _cors_allow_origins.

        self._cors_allow_methods = (
            allow_methods if allow_methods != None else self._cors_allow_methods
        )  # Set _cors_allow_methods.

        self._cors_allow_headers = (
            allow_headers if allow_headers != None else self._cors_allow_headers
        )  # Set _cors_allow_headers.

        self._cors_allow_credentials = allow_credentials  # Set _cors_allow_credentials.

        self._cors_middleware_enabled = True  # Enable CORS middleware.

        logger.info("CORS middleware enabled with specified settings")

        return

    def process_request(
        self, request_data: str, fileno: int
    ) -> tuple[str, Literal[False]] | tuple[dict, Literal[True]]:
        """
        Processes the full request, parsing each individual part of the request and then validating it.
        This method also provides the bad request response (if invalid) and the headers if the request is valid,
        so a handshake can be initiated.

        Args:
            request_data str: The full request in str format.
            fileno int: The current Client's fileno.

        Returns:
            tuple[str, Literal[False]] denoting [full_response, False representing a bad request],
            or tuple[dict, Literal[True]] denoting [headers, True representing a valid request]
        """

        response_body = "<html><body><h1>This Server only accepts WebSocket connections.</h1></body></html>"  # Set invalid response.
        response_headers = f"HTTP/1.1 {HTTPStatus.BAD_REQUEST}\r\nContent-Length: {len(response_body)}\r\n\r\n"  # Set invalid response.

        full_response = (
            response_headers + response_body
        )  # Create full invalid response.

        self.request_data = request_data  # Set full request data to class attribute.

        print(request_data)

        request: tuple = self._parse_request(
            request_data=request_data
        )  # Parse the request.

        (
            method,
            target,
            headers,
            http_version,
        ) = request  # Retrieve each individual attribute.

        # Set each value to class attribute for use at higher levels.
        self.method = method
        self.target = target
        self.headers = headers
        self.http_version = http_version

        cors_validation = self._cors_validation(
            method=method, headers=headers
        )  # Validate CORS policy.

        if not cors_validation[1]:  # Check if valid.
            return cors_validation  # If not return the invalid response.

        if not request or not self._check_if_ws_request(
            method=method, target=target
        ):  # Check if a request is present and that it is a websocket request.
            return full_response, False  # If not return bad request response and False.

        logger.info(f"Handling WebSocket handshake request fom Client: {fileno}")

        if not self._validate_handshake(
            headers=headers, http_version=http_version
        ):  # Validate the handshake request.
            logger.warning(f"Handshake from Client: {fileno}, invalid")
            return full_response, False  # If not return bad request response and False.

        logger.success(f"Handshake from Client: {fileno}, valid")

        # If valid return headers and True.
        return headers, True
