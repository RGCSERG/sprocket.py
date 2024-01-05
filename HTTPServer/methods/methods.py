from typing import List, Final

__all__: Final[List[str]] = ["Methods"]


class Methods:
    GET: str = "GET"
    HEAD: str = "HEAD"
    POST: str = "POST"
    PUT: str = "PUT"
    DELETE: str = "DELETE"
    CONNECT: str = "CONNECT"
    OPTIONS: str = "OPTIONS"
    TRACE: str = "TRACE"
    PATCH: str = "PATCH"
